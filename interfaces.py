from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from config import AgentConfig


class MemoryServiceProtocol(Protocol):
    """Protocol for memory service implementations"""

    @property
    def is_enabled(self) -> bool:
        """Check if memory service is enabled and available"""
        ...

    def retrieve_memories(self, user_input: str, user_id: str) -> str:
        """Retrieve relevant memories for user input"""
        ...

    def store_conversation(self, user_input: str, assistant_response: str, user_id: str) -> None:
        """Store conversation in memory"""
        ...


class ObservabilityServiceProtocol(Protocol):
    """Protocol for observability service operations"""

    @property
    def is_enabled(self) -> bool:
        """Check if observability service is enabled"""
        ...

    def observe_request(self, input_data: str, metadata: dict[str, Any]) -> None:
        """Start observing a request"""
        ...

    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Observe tool execution"""
        ...

    def observe_llm_call(self, model_name: str, messages: list[dict], metadata: dict[str, Any] = None) -> Any:
        """Create a child span for LLM API calls and return a context manager"""
        ...

    def update_llm_observation(self, llm_span: Any, output: Any, usage: dict[str, Any] = None) -> None:
        """Update an LLM observation with output and usage data"""
        ...

    def update_observation(self, output: Any) -> None:
        """Update current observation"""
        ...

    def flush_traces(self) -> None:
        """Flush any pending traces"""
        ...

    def get_observe_decorator(self, name: str):
        """Get the observe decorator for function decoration"""
        ...


class ToolExecutorProtocol(Protocol):
    """Protocol for tool execution implementations"""

    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with given input"""
        ...


class ConversationHandlerProtocol(Protocol):
    """Protocol for conversation handling implementations"""

    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """Process a user message and return response"""
        ...

    def clear_history(self) -> None:
        """Clear conversation history"""
        ...

    @property
    def conversation_length(self) -> int:
        """Get current conversation length"""
        ...


class ConfigValidatorProtocol(Protocol):
    """Protocol for configuration validation"""

    def validate(self, config: "AgentConfig") -> list[str]:
        """Validate configuration and return list of errors"""
        ...
