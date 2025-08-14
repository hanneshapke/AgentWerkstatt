from abc import ABC, abstractmethod
from typing import Any


class Message:
    """Represents a message in a conversation."""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class MemoryServiceProtocol(ABC):
    """Defines the interface for a memory service."""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Returns True if the memory service is active, False otherwise."""
        raise NotImplementedError

    @abstractmethod
    def retrieve_memories(self, user_input: str, user_id: str) -> str:
        """Retrieves relevant memories based on the user's input."""
        raise NotImplementedError

    @abstractmethod
    def store_conversation(self, user_input: str, assistant_response: str, user_id: str):
        """Stores a completed conversation turn in memory."""
        raise NotImplementedError


class ObservabilityServiceProtocol(ABC):
    """Defines the interface for an observability and tracing service."""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Returns True if the observability service is active, False otherwise."""
        raise NotImplementedError

    @abstractmethod
    def observe_request(self, input_data: str, metadata: dict[str, Any]):
        """Starts observing a top-level request."""
        raise NotImplementedError

    @abstractmethod
    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Starts observing a tool execution and returns a span/trace object."""
        raise NotImplementedError

    @abstractmethod
    def update_tool_observation(self, tool_observation: Any, output: Any):
        """Updates the tool observation with the execution's output."""
        raise NotImplementedError

    @abstractmethod
    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] | None = None
    ) -> Any:
        """Starts observing an LLM call and returns a span/generation object."""
        raise NotImplementedError

    @abstractmethod
    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] | None = None
    ):
        """Updates the LLM observation with the model's output and token usage."""
        raise NotImplementedError

    @abstractmethod
    def update_observation(self, output: Any):
        """Updates the current top-level observation with the final output."""
        raise NotImplementedError

    @abstractmethod
    def flush_traces(self):
        """Ensures all pending traces are sent to the observability backend."""
        raise NotImplementedError


class ToolExecutorProtocol(ABC):
    """Defines the interface for a tool executor."""

    @abstractmethod
    def execute_tool_calls(self, assistant_message_content: list) -> tuple[list[dict], list[str]]:
        """Parses a message, executes tool calls, and returns results."""
        raise NotImplementedError


class ConversationHandlerProtocol(ABC):
    """Defines the interface for a conversation handler."""

    @abstractmethod
    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """Processes a user's message and returns the agent's response."""
        raise NotImplementedError

    @abstractmethod
    def clear_history(self):
        """Clears the current conversation history."""
        raise NotImplementedError

    @property
    @abstractmethod
    def conversation_length(self) -> int:
        """Returns the number of messages in the history."""
        raise NotImplementedError
