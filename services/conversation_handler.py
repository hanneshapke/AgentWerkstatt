from collections.abc import Callable

from absl import logging

from ..interfaces import MemoryServiceProtocol, ObservabilityServiceProtocol, ToolExecutorProtocol
from ..llms.base import BaseLLM


class ConversationHandler:
    """Handles the conversation flow, including message processing, tool execution, and memory management."""

    def __init__(
        self,
        llm: BaseLLM,
        memory_service: MemoryServiceProtocol,
        observability_service: ObservabilityServiceProtocol,
        tool_executor: ToolExecutorProtocol,
        user_id_provider: Callable[[], str] | None = None,
    ):
        self.llm = llm
        self.memory_service = memory_service
        self.observability_service = observability_service
        self.tool_executor = tool_executor
        self.user_id_provider = user_id_provider or (lambda: "default_user")

    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """
        Processes a user's message, orchestrates LLM calls and tool execution, and returns the final response.
        """
        try:
            # Get initial response from LLM
            messages = self.llm.conversation_history + [{"role": "user", "content": enhanced_input}]
            _, assistant_message_content = self.llm.process_request(messages)

            # Execute tools if requested
            tool_results, _ = self.tool_executor.execute_tool_calls(assistant_message_content)

            if not tool_results:
                # No tools used, handle as a direct text response
                final_text = self._extract_text_from_response(assistant_message_content)
                self._update_history_and_finalize(user_input, final_text, assistant_message_content)
                return final_text

            # Tools were used, get the final response from the LLM
            final_response_content = self._get_final_response_after_tools(
                messages, assistant_message_content, tool_results
            )
            final_text = self._extract_text_from_response(final_response_content)

            # Update history with the full exchange
            self.llm.conversation_history.extend(
                [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": assistant_message_content},
                    {"role": "user", "content": self._format_tool_results(tool_results)},
                    {"role": "assistant", "content": final_response_content},
                ]
            )
            self._finalize_conversation(user_input, final_text)

            return final_text

        except Exception as e:
            logging.error(f"Error processing message: {e}", exc_info=True)
            self._update_observability_with_error(str(e))
            return "I apologize, but I encountered an error. Please try again."

    def _get_final_response_after_tools(self, messages, assistant_message_content, tool_results):
        """Builds the conversation with tool results and gets the final LLM response."""
        conversation = messages + [
            {"role": "assistant", "content": assistant_message_content},
            {"role": "user", "content": self._format_tool_results(tool_results)},
        ]
        final_response = self.llm.make_api_request(self._sanitize_conversation(conversation))
        if "error" in final_response:
            raise RuntimeError(f"Error getting final response from LLM: {final_response['error']}")
        return final_response.get("content", [])

    def _update_history_and_finalize(self, user_input, response_text, assistant_message_content):
        """Updates conversation history for non-tool responses and finalizes."""
        self.llm.conversation_history.extend(
            [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_message_content},
            ]
        )
        self._finalize_conversation(user_input, response_text)

    def _finalize_conversation(self, user_input: str, response_text: str):
        """Stores conversation in memory and updates observability."""
        try:
            user_id = self.user_id_provider()
            self.memory_service.store_conversation(user_input, response_text, user_id)
        except Exception as e:
            logging.warning(f"Failed to store conversation in memory: {e}")

        self.observability_service.update_observation(response_text)
        self.observability_service.flush_traces()

    def enhance_input_with_memory(self, user_input: str) -> str:
        """Enhances user input with relevant memories."""
        try:
            user_id = self.user_id_provider()
            memory_context = self.memory_service.retrieve_memories(user_input, user_id)
            return f"{memory_context}\n\nUser query: {user_input}" if memory_context else user_input
        except Exception as e:
            logging.warning(f"Failed to enhance input with memory: {e}")
            return user_input

    def _update_observability_with_error(self, error_msg: str):
        """Updates observability with error information."""
        self.observability_service.update_observation({"error": error_msg})
        self.observability_service.flush_traces()

    @staticmethod
    def _extract_text_from_response(content: list[dict]) -> str:
        """Extracts all text parts from an LLM response content."""
        return "".join(block.get("text", "") for block in content if block.get("type") == "text")

    @staticmethod
    def _format_tool_results(tool_results: list[dict]) -> list[dict]:
        """Filters for valid tool result dictionaries."""
        return [
            res
            for res in tool_results
            if isinstance(res, dict) and res.get("type") == "tool_result"
        ]

    @staticmethod
    def _sanitize_conversation(messages: list[dict]) -> list[dict]:
        """Ensures all messages in the conversation have the correct format."""
        sanitized = []
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                sanitized.append(msg)
            else:
                logging.warning(f"Skipping malformed message: {msg}")
        return sanitized

    def clear_history(self):
        """Clears the conversation history."""
        self.llm.clear_history()

    @property
    def conversation_length(self) -> int:
        """Returns the number of messages in the conversation history."""
        return len(self.llm.conversation_history)
