"""Mock LLM implementation for testing purposes"""

from typing import Any

from ..interfaces import Message

from .base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing that doesn't require API keys or external dependencies"""

    def __init__(
        self,
        model_name: str = "mock-model",
        persona: str = "Test agent",
        tools: list[Any] = None,
        responses: list[Message] = None,
    ):
        """Initialize mock LLM without calling parent __init__ to avoid API key validation"""
        self.model_name = model_name
        self.persona = persona
        self.tools = tools or []
        self.conversation_history = []
        self.system_message = f"You are {persona}. You are a helpful assistant."
        self.responses = responses or []
        self.response_index = 0
        self.observability_service = None

    def make_api_request(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Mock API request that returns a predictable response"""
        # Check if this is a follow-up call after tool execution
        has_tool_results = any(
            isinstance(msg.get("content"), list)
            and any(block.get("type") == "tool_result" for block in msg["content"])
            for msg in messages
        )

        if has_tool_results:
            # This is a follow-up call after tool execution, provide final response
            tool_result_content = ""
            for msg in messages:
                if isinstance(msg.get("content"), list):
                    for block in msg["content"]:
                        if block.get("type") == "tool_result":
                            content = block.get("content", "")
                            if isinstance(content, str) and "static tool output" in content:
                                tool_result_content = content
                                break

            return {
                "content": [
                    {"type": "text", "text": f"Based on the tool result: {tool_result_content}"}
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }

        # Use predefined responses if available
        elif self.responses and self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return {
                "content": [{"type": "text", "text": response.content}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        # Look for static_tool specifically for testing
        elif any(
            tool.get_name() == "static_tool" for tool in self.tools if hasattr(tool, "get_name")
        ):
            return {
                "content": [
                    {"type": "text", "text": "I'll use the static tool."},
                    {
                        "type": "tool_use",
                        "id": "mock_tool_id_123",
                        "name": "static_tool",
                        "input": {},
                    },
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        # If we have tools, simulate using the first one
        elif self.tools:
            tool = self.tools[0]
            return {
                "content": [
                    {"type": "text", "text": f"I'll use the {tool.name} tool."},
                    {
                        "type": "tool_use",
                        "id": "mock_tool_id_123",
                        "name": tool.get_name(),
                        "input": {},
                    },
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        else:
            # Default mock response
            return {
                "content": [{"type": "text", "text": "Mock response"}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }

    def process_request(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process a request and return mock response"""
        response = self.make_api_request(messages)
        assistant_message = response.get("content", [])
        return messages, assistant_message

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
