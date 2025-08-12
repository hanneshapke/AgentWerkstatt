import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from .interfaces import ConfigValidatorProtocol


@dataclass
class AgentConfig:
    """Configuration for the Agent"""

    model: str = ""
    tools_dir: str = ""
    verbose: bool = False
    persona: str = ""
    langfuse_enabled: bool = False
    langfuse_project_name: str = "agentwerkstatt"
    memory_enabled: bool = False
    memory_model_name: str = "gpt-4o-mini"
    memory_server_url: str = "http://localhost:8000"

    @classmethod
    def from_persona(cls, persona_file: str) -> "AgentConfig":
        """Load configuration from persona file"""
        with open(persona_file, encoding="utf-8") as f:
            return cls(persona=f.read().strip())

    @classmethod
    def from_yaml(cls, file_path: str) -> "AgentConfig":
        """Load configuration from YAML file"""
        with open(file_path) as f:
            data = yaml.safe_load(f)

        # Load persona content from file if a filename is specified
        if data.get("persona"):
            # If persona is specified as a filename, load its content
            persona_file = data["persona"]
            if not os.path.isabs(persona_file):
                # If relative path, resolve relative to config file
                config_dir = Path(file_path).parent
                persona_file = config_dir / persona_file
            data["persona"] = cls.from_persona(str(persona_file)).persona
        else:
            # Fall back to default persona file relative to config file
            config_dir = Path(file_path).parent
            default_persona_file = config_dir / "agent.md"
            if default_persona_file.exists():
                data["persona"] = cls.from_persona(str(default_persona_file)).persona
            else:
                # If no agent.md in config dir, try agents.md in project root
                data["persona"] = cls.from_persona("agents.md").persona

        # Handle nested langfuse config - flatten it into the main config
        langfuse_data = data.pop("langfuse", {})
        if langfuse_data:
            data["langfuse_enabled"] = langfuse_data.get("enabled", False)
            data["langfuse_project_name"] = langfuse_data.get("project_name", "agentwerkstatt")

        # Handle nested memory config - flatten it into the main config
        memory_data = data.pop("memory", {})
        if memory_data:
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
        if not config.persona:
            errors.append("Agent persona content is required but is empty or missing")

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
