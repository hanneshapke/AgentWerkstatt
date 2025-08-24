from abc import ABC, abstractmethod
from typing import Any

from .schemas import ToolSchema


class BaseTool(ABC):
    """Abstract base class for all tools available to the agent."""

    @abstractmethod
    def get_name(self) -> str:
        """Returns the programmatic name of the tool (e.g., 'web_search')."""
        raise NotImplementedError

    @abstractmethod
    def get_description(self) -> str:
        """Returns a human-readable description of what the tool does."""
        raise NotImplementedError

    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """
        Returns the JSON schema for the tool's inputs, as required by the LLM.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Executes the tool with the given keyword arguments and returns a result dictionary.
        """
        raise NotImplementedError
