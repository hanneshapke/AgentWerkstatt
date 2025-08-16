from collections.abc import Callable
from typing import TYPE_CHECKING

from absl import logging

from ..interfaces import (
    ConversationHandlerProtocol,
    MemoryServiceProtocol,
    ObservabilityServiceProtocol,
)
from ..llms.base import BaseLLM
from .history_manager import HistoryManager
from .response_message_formatter import ResponseMessageFormatter
from .tool_interaction_handler import ToolInteractionHandler

if TYPE_CHECKING:
    from ..agent import Agent


class ConversationHandler(ConversationHandlerProtocol):
    """Handles the conversation flow, including message processing, tool execution, and memory management."""

    def __init__(
        self,
        llm: BaseLLM,
        agent: "Agent",
        memory_service: MemoryServiceProtocol,
        observability_service: ObservabilityServiceProtocol,
        tool_interaction_handler: ToolInteractionHandler,
        user_id_provider: Callable[[], str] | None = None,
    ):
        self.llm = llm
        self.agent = agent
        self.memory_service = memory_service
        self.observability_service = observability_service
        self.tool_interaction_handler = tool_interaction_handler
        self.user_id_provider = user_id_provider or (lambda: "default_user")
        self.history_manager = HistoryManager()
        self.response_formatter = ResponseMessageFormatter(agent.active_persona_name)

    def enhance_input_with_memory(self, user_input: str) -> str:
        """Enhances user input with relevant memories."""
        try:
            user_id = self.user_id_provider()
            memory_context = self.memory_service.retrieve_memories(user_input, user_id)
            return f"{memory_context}\n\nUser query: {user_input}" if memory_context else user_input
        except Exception as e:
            logging.warning(f"Failed to enhance input with memory: {e}")
            return user_input

    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """
        Processes a user's message, orchestrates LLM calls and tool execution, and returns the final response.
        """
        try:
            messages = self.history_manager.get_history() + [
                {"role": "user", "content": enhanced_input}
            ]
            _, assistant_message_content = self.llm.process_request(messages)

            tool_results, _ = self.tool_interaction_handler.handle_tool_calls(
                assistant_message_content
            )

            if not tool_results:
                final_text = self.response_formatter.extract_text_from_response(
                    assistant_message_content
                )
                self.history_manager.add_message("user", user_input)
                self.history_manager.add_message("assistant", final_text)
                self._finalize_conversation(user_input, final_text)
                return final_text
            else:
                return self._handle_tool_response(
                    messages, assistant_message_content, tool_results, user_input
                )

        except Exception as e:
            logging.error(f"Critical error in message processing: {e}")
            return self._create_error_response(user_input, str(e))

    def _handle_tool_response(
        self,
        messages: list[dict],
        assistant_message: list[dict],
        tool_results: list[dict],
        user_input: str,
    ) -> str:
        """Handle response when tools were executed"""
        conversation = messages + [
            {"role": "assistant", "content": assistant_message},
            {"role": "user", "content": tool_results},
        ]

        final_response = self.llm.make_api_request(conversation)
        if "error" in final_response:
            return f"❌ Error getting final response: {final_response['error']}"

        final_text = self.response_formatter.extract_text_from_response(
            final_response.get("content", [])
        )
        final_text_with_persona = self.response_formatter.prepend_persona_to_response(final_text)

        self.history_manager.add_message("user", user_input)
        self.history_manager.add_message("assistant", final_text_with_persona)

        self._finalize_conversation(user_input, final_text_with_persona)

        return final_text_with_persona

    def _finalize_conversation(self, user_input: str, response_text: str):
        """Stores conversation in memory and updates observability."""
        try:
            user_id = self.user_id_provider()
            self.memory_service.store_conversation(user_input, response_text, user_id)
        except Exception as e:
            logging.warning(f"Failed to store conversation in memory: {e}")

        self.observability_service.update_observation(response_text)
        self.observability_service.flush_traces()

    def _create_error_response(self, user_input: str, error_msg: str) -> str:
        """Create a formatted error response."""
        response = f"❌ Error processing request: {error_msg}"
        self._finalize_conversation(user_input, response)
        return response

    def clear_history(self):
        """Clears the conversation history."""
        self.history_manager.clear_history()

    @property
    def conversation_length(self) -> int:
        """Returns the number of messages in the conversation history."""
        return self.history_manager.conversation_length
