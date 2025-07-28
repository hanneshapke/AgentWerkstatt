"""Mock LLM implementation for testing purposes"""

from typing import Any

from .base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing that doesn't require API keys or external dependencies"""

    def __init__(
        self,
        model_name: str = "mock-model",
        agent_objective: str = "Test agent",
        tools: list[dict] = None,
    ):
        """Initialize mock LLM without calling parent __init__ to avoid API key validation"""
        self.model_name = model_name
        self.agent_objective = agent_objective
        self.tools = tools or []
        self.conversation_history = []
        self.system_message = f"You are {agent_objective}. You are a helpful assistant."

    def make_api_request(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Mock API request that returns a predictable response"""
        return {
            "content": [{"type": "text", "text": "Mock API response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

    def process_request(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process a request and return mock response"""
        # Mock assistant response
        assistant_message = [{"type": "text", "text": "Mock response"}]
        return messages, assistant_message

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
