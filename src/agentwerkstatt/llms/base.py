from abc import ABC, abstractmethod
from typing import Any

from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()


class BaseLLM(ABC):
    """Abstract base class for all Large Language Models."""

    def __init__(
        self,
        model_name: str,
        tools: list[Any] | None = None,
        persona: str = "",
        observability_service=None,
    ):
        self.model_name = model_name
        self.tools = tools or []
        self.persona = persona
        self.observability_service = observability_service
        self.conversation_history: list[dict] = []
        self.timeout = 30.0

    @abstractmethod
    def set_persona(self, persona: str):
        """Set the persona for the LLM"""
        raise NotImplementedError("Subclasses must implement this method")

    def clear_history(self):
        """Clears the conversation history."""
        self.conversation_history = []

    def _validate_api_key(self, api_key_name: str):
        """
        Validates that the specified API key is set as an environment variable.
        Raises:
            ValueError: If the API key environment variable is not set.
        """
        import os

        if not os.getenv(api_key_name):
            raise ValueError(f"'{api_key_name}' environment variable is required but not set.")

    def _get_tool_schemas(self) -> list[dict]:
        """Returns the JSON schema for each registered tool."""
        return [tool.get_schema() for tool in self.tools]

    @abstractmethod
    def make_api_request(self, messages: list[dict]) -> dict:
        """
        Makes a raw API request to the LLM.
        Subclasses must implement this method to handle the specific API protocol.
        """
        raise NotImplementedError

    @abstractmethod
    def process_request(self, messages: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Processes a user request by sending it to the LLM and returning the conversation history and response.
        """
        raise NotImplementedError

    @abstractmethod
    def query(self, prompt: str, context: str) -> str:
        """
        Sends a query to the language model and returns the response.
        """
        pass

    @abstractmethod
    def get_info(self) -> dict:
        """
        Returns information about the model.
        """
        pass
