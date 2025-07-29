from abc import ABC, abstractmethod
from typing import Any


class MemoryServiceProtocol(ABC):
    """Protocol for memory service implementations"""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the memory service is enabled"""
        pass

    @abstractmethod
    def retrieve_memories(self, user_input: str, user_id: str) -> str:
        """Retrieve relevant memories for the user input"""
        pass

    @abstractmethod
    def store_conversation(self, user_input: str, assistant_response: str, user_id: str) -> None:
        """Store a conversation in memory"""
        pass


class ObservabilityServiceProtocol(ABC):
    """Protocol for observability service implementations"""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the observability service is enabled"""
        pass

    @abstractmethod
    def observe_request(self, input_data: str, metadata: dict[str, Any]) -> None:
        """Start observing a request"""
        pass

    @abstractmethod
    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Start observing tool execution, return observation object"""
        pass

    @abstractmethod
    def update_tool_observation(self, tool_observation: Any, output: Any) -> None:
        """Update tool observation with output"""
        pass

    @abstractmethod
    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] = None
    ) -> Any:
        """Start observing an LLM call, return observation object"""
        pass

    @abstractmethod
    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] = None
    ) -> None:
        """Update LLM observation with output and usage"""
        pass

    @abstractmethod
    def update_observation(self, output: Any) -> None:
        """Update current observation with output"""
        pass

    @abstractmethod
    def flush_traces(self) -> None:
        """Flush any pending traces"""
        pass

    @abstractmethod
    def get_observe_decorator(self, name: str):
        """Get observe decorator for function decoration"""
        pass


class ToolExecutorProtocol(ABC):
    """Protocol for tool execution implementations"""

    @abstractmethod
    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with given input"""
        pass


class ConversationHandlerProtocol(ABC):
    """Protocol for conversation handling implementations"""

    @abstractmethod
    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """Process a user message and return response"""
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """Clear conversation history"""
        pass

    @property
    @abstractmethod
    def conversation_length(self) -> int:
        """Get current conversation length"""
        pass


class ConfigValidatorProtocol(ABC):
    """Protocol for configuration validation"""

    @abstractmethod
    def validate(self, config: "AgentConfig") -> list[str]:
        """Validate configuration and return list of errors"""
        pass
