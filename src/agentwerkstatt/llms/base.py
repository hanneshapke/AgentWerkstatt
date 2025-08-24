from abc import ABC, abstractmethod
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from a .env file if it exists
load_dotenv()


class ToolCall(BaseModel):
    tool: str = Field(
        description="Name of the tool to use. Must be one of the tools registered with the tool registry."
    )
    input: dict = Field(description="Tool-specific input parameters. Must be a valid JSON object.")


class LLMResponse(BaseModel):
    """Represents a response from the LLM."""

    reasoning: str = Field(description="What are your thoughts about the next step?")
    tool_call: ToolCall | None = Field(
        description="What tool call should be made? If no tool call is needed, return an empty string.",
        default=None,
    )
    message_to_user: str = Field(
        description="Provide a brief message of your thoughts to the user."
    )
    final_answer: str = Field(
        description="Provide a final answer to the user's question when you have all the information you need."
    )


class BaseLLM(ABC):
    """Abstract base class for all Large Language Models."""

    def __init__(
        self,
        model_name: str,
        tools: list[Any] | None = None,
        observability_service=None,
        **kwargs,
    ):
        self.model_name = model_name
        self.tools = tools or []
        self.observability_service = observability_service
        self.conversation_history: list[dict] = []
        self.timeout = 30.0

    def clear_history(self):
        """Clears the conversation history."""
        self.conversation_history = []

    def get_tool_descriptions(self) -> str:
        """Returns a string of tool descriptions."""
        return "\n".join([f"* {tool.get_name()}: {tool.get_description()}" for tool in self.tools])

    def set_system_prompt(self, system_prompt: str):
        """Sets the system prompt for the LLM."""
        self.system_prompt = system_prompt

    def _validate_api_key(self, api_key_name: str):
        """
        Validates that the specified API key is set as an environment variable.
        Raises:
            ValueError: If the API key environment variable is not set.
        """
        import os

        if not os.getenv(api_key_name):
            raise ValueError(f"'{api_key_name}' environment variable is required but not set.")

    @abstractmethod
    def _get_tool_schemas(self) -> list[dict]:
        """Returns the JSON schema for each registered tool."""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def make_api_request(self, messages: list[dict]) -> dict:
        """
        Makes a raw API request to the LLM.
        Subclasses must implement this method to handle the specific API protocol.
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
