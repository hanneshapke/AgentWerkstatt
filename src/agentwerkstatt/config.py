import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, DirectoryPath, field_validator, model_validator
from pydantic_settings import BaseSettings
import yaml


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


class LLMConfig(BaseModel):
    """Configuration for the LLM."""

    provider: Literal["claude", "ollama", "lmstudio", "gemini", "gpt-oss"] = "claude"
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096


class AgentConfig(BaseSettings):
    """Configuration for the Agent."""

    llm: LLMConfig
    tools_dir: DirectoryPath
    verbose: bool = False
    max_iterations: int = 10
    task_objective: str = ""
    # TODO: add langfuse and memory config
    # langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)
    # memory: MemoryConfig = Field(default_factory=MemoryConfig)

    @field_validator("task_objective", mode="before")
    @classmethod
    def validate_task_objective(cls, v: str) -> str:  # noqa: N805
        if not v:
            raise ValueError("task_objective is required")
        return v

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
