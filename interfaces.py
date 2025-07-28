from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, List, Optional, TYPE_CHECKING

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
    """Protocol for observability service implementations"""

    @property
    def is_enabled(self) -> bool:
        """Check if observability service is enabled"""
        ...

    def observe_request(self, input_data: str, metadata: Dict[str, Any]) -> None:
        """Start observing a request"""
        ...

    def observe_tool_execution(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """Observe tool execution"""
        ...

    def update_observation(self, output: Any) -> None:
        """Update current observation with output"""
        ...

    def flush_traces(self) -> None:
        """Flush any pending traces"""
        ...


class ToolExecutorProtocol(Protocol):
    """Protocol for tool execution implementations"""

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
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

    def validate(self, config: "AgentConfig") -> List[str]:
        """Validate configuration and return list of errors"""
        ...
