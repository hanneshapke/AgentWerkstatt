import os
from pathlib import Path
from typing import ClassVar

import yaml
from pydantic import BaseModel, Field, DirectoryPath, field_validator, model_validator
from pydantic_settings import BaseSettings


class PersonaConfig(BaseModel):
    """Configuration for a single persona."""

    id: str
    name: str
    description: str
    file: str
    config: dict = Field(default_factory=dict)


class LangfuseConfig(BaseModel):
    """Configuration for Langfuse."""

    enabled: bool = False
    project_name: str = "agentwerkstatt"

    @model_validator(mode="after")
    def check_env_vars(self) -> "LangfuseConfig":
        if self.enabled:
            if not os.getenv("LANGFUSE_PUBLIC_KEY"):
                raise ValueError(
                    "LANGFUSE_PUBLIC_KEY environment variable is required when langfuse is enabled."
                )
            if not os.getenv("LANGFUSE_SECRET_KEY"):
                raise ValueError(
                    "LANGFUSE_SECRET_KEY environment variable is required when langfuse is enabled."
                )
        return self


class MemoryConfig(BaseModel):
    """Configuration for Memory."""

    enabled: bool = False
    model_name: str = "gpt-4o-mini"
    server_url: str = "http://localhost:8000"


class AgentConfig(BaseSettings):
    """Configuration for the Agent."""

    model: str
    tools_dir: DirectoryPath
    verbose: bool = False
    personas: list[PersonaConfig] = Field(default_factory=list)
    default_persona: str = "default"
    langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    _config_dir: ClassVar[Path] = Path.cwd()

    @field_validator("personas", mode="before")
    @classmethod
    def load_persona_files(cls, personas_data: list[dict]) -> list[dict]:
        """Load persona content from files."""
        if not isinstance(personas_data, list):
            return personas_data

        loaded_personas = []
        for persona_data in personas_data:
            if not isinstance(persona_data, dict):
                loaded_personas.append(persona_data)
                continue

            persona_file = persona_data.get("file")
            if not persona_file:
                raise ValueError("Persona configuration must have a 'file' key.")

            if not os.path.isabs(persona_file):
                persona_file_path = cls._config_dir / persona_file
            else:
                persona_file_path = Path(persona_file)

            if not persona_file_path.exists():
                raise FileNotFoundError(
                    f"Persona file not found for '{persona_data.get('id', 'unknown')}': {persona_file_path}"
                )

            with open(persona_file_path, encoding="utf-8") as f:
                persona_data["file"] = f.read().strip()
            loaded_personas.append(persona_data)
        return loaded_personas

    @model_validator(mode="after")
    def check_default_persona(self) -> "AgentConfig":
        # If default_persona is specified but no personas are defined, raise an error
        if self.default_persona and not self.personas:
            raise ValueError(
                "Configuration must contain a 'personas' section when default_persona is specified."
            )

        # If personas exist, ensure the default_persona exists in the list
        if self.personas and self.default_persona not in [p.id for p in self.personas]:
            raise ValueError(
                f"Default persona '{self.default_persona}' not found in loaded personas."
            )
        return self

    @classmethod
    def from_yaml(cls, file_path: str) -> "AgentConfig":
        """Load configuration from YAML file."""
        config_path = Path(file_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {file_path}")

        cls._config_dir = config_path.parent

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML format in {file_path}")

        return cls(**data)


def get_config(config_path: str = None) -> AgentConfig:
    """
    Load and validate the agent configuration from a YAML file.

    Args:
        config_path (str, optional): The path to the configuration file.
            If not provided, it defaults to 'config.yaml' in the current directory.

    Returns:
        AgentConfig: The loaded and validated agent configuration.

    Raises:
        FileNotFoundError: If the configuration file is not found.
        ValueError: If the configuration is invalid.
    """
    if config_path is None:
        config_path = "config.yaml"

    return AgentConfig.from_yaml(config_path)
