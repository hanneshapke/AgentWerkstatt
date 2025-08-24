"""Mock LLM implementation for testing purposes"""

from typing import Any, TYPE_CHECKING

from .base import BaseLLM

if TYPE_CHECKING:
    from ..main import Messages


class MockLLM(BaseLLM):
    """Mock LLM for testing that doesn't require API keys or external dependencies"""

    def __init__(
        self,
        model_name: str = "mock-model",
        tools: list[Any] = None,
        responses: "Messages | None" = None,
        **kwargs,
    ):
        """Initialize mock LLM without calling parent __init__ to avoid API key validation"""
        super().__init__(model_name, tools, **kwargs)
        self.system_message = "You are a helpful assistant."
        self.responses = responses.messages if responses else []
        self.response_index = 0

    def make_api_request(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Mock API request that returns a predictable response."""
        # Check if this is a follow-up call after tool execution
        has_tool_results = any(
            isinstance(msg.get("content"), list)
            and any(block.get("type") == "tool_result" for block in msg["content"])
            for msg in messages
        )

        if has_tool_results:
            # This is a follow-up call after tool execution, provide final response
            return {
                "content": [{"type": "text", "text": "static tool output"}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }

        # Use predefined responses if available
        if self.responses and self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return {
                "content": [{"type": "text", "text": response.content}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }

        # If we have tools, simulate using the first one
        if self.tools:
            tool = self.tools[0]
            return {
                "content": [
                    {"type": "text", "text": f"I'll use the {tool.get_name()} tool."},
                    {
                        "type": "tool_use",
                        "id": "mock_tool_id_123",
                        "name": tool.get_name(),
                        "input": {},
                    },
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }

        # Default mock response
        return {
            "content": [{"type": "text", "text": "Mock response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

    def query(self, prompt: str, context: str = "") -> str:
        """
        Sends a query to the language model and returns the response.
        """
        return "Mock query response"

    def process_request(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process a request and return mock response"""
        response = self.make_api_request(messages)
        assistant_message = response.get("content", [])
        return messages, assistant_message

    def get_info(self) -> dict:
        """
        Returns information about the model.
        """
        return {"model": self.model_name}
