import os
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class AgentConfig:
    """Configuration for the Agent, loaded from a YAML file."""
    model: str
    tools_dir: str
    persona: str
    verbose: bool = False
    langfuse_enabled: bool = False
    langfuse_project_name: str = "agentwerkstatt"
    memory_enabled: bool = False
    memory_model_name: str = "gpt-4o-mini"
    memory_server_url: str = "http://localhost:8000"

    @classmethod
    def from_yaml(cls, file_path: str) -> "AgentConfig":
        """Load configuration from YAML file, validate, and return an instance."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise ValueError(f"Configuration file not found at: {file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

        # Process nested configurations
        cls._process_nested_configs(data)

        # Load persona content
        data['persona'] = cls._load_persona(data.get('persona'), Path(file_path).parent)

        config = cls(**data)
        config._validate()
        return config

    @staticmethod
    def _process_nested_configs(data: dict):
        """Flatten nested configuration sections (langfuse, memory) into the main config data."""
        if 'langfuse' in data:
            langfuse_data = data.pop('langfuse')
            data['langfuse_enabled'] = langfuse_data.get('enabled', False)
            data['langfuse_project_name'] = langfuse_data.get('project_name', 'agentwerkstatt')

        if 'memory' in data:
            memory_data = data.pop('memory')
            data['memory_enabled'] = memory_data.get('enabled', False)
            data['memory_model_name'] = memory_data.get('model_name', 'gpt-4o-mini')
            data['memory_server_url'] = memory_data.get('server_url', 'http://localhost:8000')

    @staticmethod
    def _load_persona(persona_path: str | None, config_dir: Path) -> str:
        """Load persona content from a file or return the default."""
        if persona_path:
            # If persona is specified as a filename, load its content
            persona_file = Path(persona_path)
            if not persona_file.is_absolute():
                persona_file = config_dir / persona_file
            
            if persona_file.exists():
                return persona_file.read_text(encoding="utf-8").strip()
            else:
                raise ValueError(f"Specified persona file not found: {persona_file}")

        # Fallback to default persona files
        default_persona_file = config_dir / "agent.md"
        if default_persona_file.exists():
            return default_persona_file.read_text(encoding="utf-8").strip()
        
        root_persona_file = Path("agents.md")
        if root_persona_file.exists():
            return root_persona_file.read_text(encoding="utf-8").strip()

        raise ValueError("Agent persona is not defined in config and default persona files ('agent.md', 'agents.md') were not found.")

    def _validate(self):
        """Validate configuration and raise ValueError on failure."""
        errors = []
        if not self.model:
            errors.append("Model name is required.")
        if not self.tools_dir:
            errors.append("Tools directory is required.")
        elif not Path(self.tools_dir).exists():
            errors.append(f"Tools directory does not exist: {self.tools_dir}")
        if not self.persona:
            errors.append("Agent persona content is required but is empty or missing.")

        if self.langfuse_enabled:
            for var in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]:
                if not os.getenv(var):
                    errors.append(f"Langfuse is enabled but missing environment variable: {var}")
        
        if self.memory_enabled:
            if not self.memory_server_url:
                errors.append("Memory server URL is required when memory is enabled.")
            if not self.memory_model_name:
                errors.append("Memory model name is required when memory is enabled.")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors)
            raise ValueError(error_msg)

