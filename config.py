import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from interfaces import ConfigValidatorProtocol


@dataclass
class AgentConfig:
    """Configuration for the Agent"""

    model: str = ""
    tools_dir: str = ""
    verbose: bool = False
    personas: dict[str, str] = field(default_factory=dict)
    default_persona: str = "default"
    langfuse_enabled: bool = False
    langfuse_project_name: str = "agentwerkstatt"
    memory_enabled: bool = False
    memory_model_name: str = "gpt-4o-mini"
    memory_server_url: str = "http://localhost:8000"

    @classmethod
    def from_persona_file(cls, persona_file: str) -> str:
        """Load persona content from a file."""
        with open(persona_file, encoding="utf-8") as f:
            return f.read().strip()

    @classmethod
    def from_yaml(cls, file_path: str) -> "AgentConfig":
        """Load configuration from YAML file"""
        with open(file_path) as f:
            data = yaml.safe_load(f)

        config_dir = Path(file_path).parent

        # Load multiple personas
        if "personas" in data:
            loaded_personas = {}
            for name, persona_path in data["personas"].items():
                persona_file = (
                    Path(persona_path) if os.path.isabs(persona_path) else config_dir / persona_path
                )
                if persona_file.exists():
                    loaded_personas[name] = cls.from_persona_file(str(persona_file))
                else:
                    print(f"Warning: Persona file not found for '{name}': {persona_file}")
            data["personas"] = loaded_personas
        # Fallback for single persona for backward compatibility
        elif data.get("persona"):
            persona_file = data["persona"]
            if not os.path.isabs(persona_file):
                persona_file = config_dir / persona_file
            data["personas"] = {"default": cls.from_persona_file(str(persona_file))}
            del data["persona"]
        else:
            # Default to agents.md
            default_persona_file = config_dir / "agents.md"
            if default_persona_file.exists():
                data["personas"] = {"default": cls.from_persona_file(str(default_persona_file))}
            else:
                data["personas"] = {"default": cls.from_persona_file("agents.md")}

        # Handle nested langfuse config - flatten it into the main config
        if "langfuse" in data:
            langfuse_data = data.pop("langfuse", {})
            data["langfuse_enabled"] = langfuse_data.get("enabled", False)
            data["langfuse_project_name"] = langfuse_data.get("project_name", "agentwerkstatt")

        # Handle nested memory config - flatten it into the main config
        if "memory" in data:
            memory_data = data.pop("memory", {})
            data["memory_enabled"] = memory_data.get("enabled", False)
            data["memory_model_name"] = memory_data.get("model_name", "gpt-4o-mini")
            data["memory_server_url"] = memory_data.get("server_url", "http://localhost:8000")

        return cls(**data)


class ConfigValidator:
    """Validates agent configuration"""

    def validate(self, config: AgentConfig, config_file_path: str = None) -> list[str]:
        """Validate configuration and return list of error messages"""
        errors = []

        # Basic validation
        if not config.model:
            errors.append("Model name is required")

        if not config.tools_dir:
            errors.append("Tools directory is required")
        elif not os.path.exists(config.tools_dir):
            errors.append(f"Tools directory does not exist: {config.tools_dir}")

        # Validate persona content
        if not config.personas:
            errors.append("Agent personas are required but none are defined.")
        elif config.default_persona not in config.personas:
            errors.append(
                f"Default persona '{config.default_persona}' not found in loaded personas."
            )

        # Langfuse validation
        if config.langfuse_enabled:
            errors.extend(self._validate_langfuse_config())

        # Memory validation
        if config.memory_enabled:
            errors.extend(self._validate_memory_config(config))

        return errors

    def _validate_langfuse_config(self) -> list[str]:
        """Validate Langfuse-specific configuration"""
        errors = []
        required_env_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]

        for var in required_env_vars:
            if not os.getenv(var):
                errors.append(f"Langfuse enabled but missing environment variable: {var}")

        return errors

    def _validate_memory_config(self, config: AgentConfig) -> list[str]:
        """Validate memory-specific configuration"""
        errors = []

        if not config.memory_server_url:
            errors.append("Memory server URL is required when memory is enabled")

        if not config.memory_model_name:
            errors.append("Memory model name is required when memory is enabled")

        return errors


class ConfigManager:
    """Manages configuration loading and validation"""

    def __init__(self, validator: ConfigValidatorProtocol = None):
        self.validator = validator or ConfigValidator()

    def load_and_validate(self, config_path: str) -> AgentConfig:
        """Load configuration from file and validate it"""
        try:
            config = AgentConfig.from_yaml(config_path)
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}") from e

        errors = self.validator.validate(config, config_path)
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"- {error}" for error in errors
            )
            raise ValueError(error_msg)

        return config
