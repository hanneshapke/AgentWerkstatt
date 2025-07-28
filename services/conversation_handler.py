from absl import logging
from collections.abc import Callable

from ..interfaces import MemoryServiceProtocol, ObservabilityServiceProtocol, ToolExecutorProtocol
from ..llms.claude import ClaudeLLM


class ConversationHandler:
    """Handles conversation flow and message processing"""

    def __init__(
        self,
        llm: ClaudeLLM,
        memory_service: MemoryServiceProtocol,
        observability_service: ObservabilityServiceProtocol,
        tool_executor: ToolExecutorProtocol,
        user_id_provider: Callable[[], str] | None = None,
    ):
        self.llm = llm
        self.memory_service = memory_service
        self.observability_service = observability_service
        self.tool_executor = tool_executor
        self.user_id_provider = user_id_provider or self._default_user_id_provider

    def _default_user_id_provider(self) -> str:
        """Default user ID provider. Can be enhanced to support multiple users."""
        return "default_user"

    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """Process a user message and return the agent's response"""

        # Create message for LLM
        user_message = {"role": "user", "content": enhanced_input}
        messages = self.llm.conversation_history + [user_message]
        messages, assistant_message = self.llm.process_request(messages)

        # Handle tool calls if present
        tool_results, final_response_parts = self.tool_executor.execute_tool_calls(
            assistant_message
        )

        if tool_results:
            # If there were tool calls, get final response from Claude
            return self._handle_tool_calls_response(
                messages, assistant_message, tool_results, user_input
            )
        else:
            # No tool calls, return the text response
            return self._handle_direct_response(assistant_message, user_input, final_response_parts)

    def _handle_tool_calls_response(
        self,
        messages: list[dict],
        assistant_message: list[dict],
        tool_results: list[dict],
        original_user_input: str,
    ) -> str:
        """Handle response when tool calls were made"""

        # Add the assistant's message with tool calls
        messages = messages + [{"role": "assistant", "content": assistant_message}]

        # Add tool results
        messages = messages + [{"role": "user", "content": tool_results}]

        # Get final response from Claude
        final_response = self.llm.make_api_request(messages)

        if "error" in final_response:
            return f"❌ Error getting final response: {final_response['error']}"

        final_content = final_response.get("content", [])
        final_text = ""
        for block in final_content:
            if block.get("type") == "text":
                final_text += block["text"]

        # Update conversation history
        self.llm.conversation_history = messages + [{"role": "assistant", "content": final_content}]

        # Store conversation in memory (using original user input, not enhanced)
        user_id = self.user_id_provider()
        self.memory_service.store_conversation(original_user_input, final_text, user_id)

        # Update observability with final output
        self.observability_service.update_observation(final_text)

        return final_text

    def _handle_direct_response(
        self,
        assistant_message: list[dict],
        original_user_input: str,
        final_response_parts: list[str],
    ) -> str:
        """Handle direct response when no tool calls were made"""

        # No tool calls, return the text response
        response_text = " ".join(final_response_parts)

        # Update conversation history (use original user_input for history, not enhanced)
        self.llm.conversation_history.append({"role": "user", "content": original_user_input})
        self.llm.conversation_history.append({"role": "assistant", "content": assistant_message})

        # Store conversation in memory (using original user input, not enhanced)
        user_id = self.user_id_provider()
        self.memory_service.store_conversation(original_user_input, response_text, user_id)

        # Update observability with final output
        self.observability_service.update_observation(response_text)

        return response_text

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.llm.clear_history()

    @property
    def conversation_length(self) -> int:
        """Get current conversation length"""
        return len(self.llm.conversation_history)

    def enhance_input_with_memory(self, user_input: str) -> str:
        """Enhance user input with relevant memories"""
        user_id = self.user_id_provider()
        memory_context = self.memory_service.retrieve_memories(user_input, user_id)

        if memory_context:
            return f"{memory_context}\nUser query: {user_input}"
        return user_input
