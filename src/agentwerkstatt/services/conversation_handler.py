from collections.abc import Callable
from typing import TYPE_CHECKING

from absl import logging

from ..interfaces import (
    ConversationHandlerProtocol,
    MemoryServiceProtocol,
    ObservabilityServiceProtocol,
    ToolExecutorProtocol,
)
from ..llms.claude import ClaudeLLM

if TYPE_CHECKING:
    from ..agent import Agent


class ConversationHandler(ConversationHandlerProtocol):
    """Handles the conversation flow, including message processing, tool execution, and memory management."""

    def __init__(
        self,
        llm: ClaudeLLM,
        agent: "Agent",
        memory_service: MemoryServiceProtocol,
        observability_service: ObservabilityServiceProtocol,
        tool_executor: ToolExecutorProtocol,
        user_id_provider: Callable[[], str] | None = None,
    ):
        self.llm = llm
        self.agent = agent
        self.memory_service = memory_service
        self.observability_service = observability_service
        self.tool_executor = tool_executor
        self.user_id_provider = user_id_provider or (lambda: "default_user")

    def _prepend_persona_to_response(self, response_text: str) -> str:
        """Prepend the active persona name to the response text."""
        return f"[{self.agent.active_persona_name}] {response_text}"

    def _prepend_persona_to_content(self, content: list[dict]) -> list[dict]:
        """Prepend the active persona name to the text blocks in a content list."""
        if not content:
            return content

        # Create a new list to avoid modifying the original
        new_content = []
        prepended = False
        for block in content:
            if block.get("type") == "text" and not prepended:
                new_block = block.copy()
                new_block["text"] = self._prepend_persona_to_response(new_block.get("text", ""))
                new_content.append(new_block)
                prepended = True
            else:
                new_content.append(block)

        # If no text block was found to prepend to, add one at the beginning
        if not prepended:
            new_content.insert(0, {"type": "text", "text": f"[{self.agent.active_persona_name}]"})

        return new_content

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
            else:
                # Tools were used, handle tool response
                return self._handle_tool_response(
                    messages, assistant_message_content, tool_results, user_input
                )

        except Exception as e:
            logging.error(f"Critical error in message processing: {e}")
            return self._create_error_response(user_input, str(e))

    def _execute_tools(self, assistant_message: list[dict]) -> tuple[list[dict], list[str]]:
        """Execute tool calls and return results"""
        try:
            tool_results, text_parts = self.tool_executor.execute_tool_calls(assistant_message)

            # Check if all tools failed
            if tool_results and all(result.get("is_error", False) for result in tool_results):
                logging.warning("All tool executions failed")
                # Still return tool results - Claude requires tool_result for every tool_use

            logging.debug(f"Tool execution completed: {len(tool_results)} results")
            return tool_results, text_parts

        except Exception as e:
            logging.error(f"Tool execution failed: {e}")
            return [], []

    def _handle_tool_response(
        self,
        messages: list[dict],
        assistant_message: list[dict],
        tool_results: list[dict],
        user_input: str,
    ) -> str:
        """Handle response when tools were executed"""
        try:
            # Build conversation with tool results
            conversation = self._build_tool_conversation(messages, assistant_message, tool_results)

            # Get final response from LLM
            final_response = self.llm.make_api_request(conversation)
            if "error" in final_response:
                return f"❌ Error getting final response: {final_response['error']}"

            # Extract text from response
            final_text = self._extract_text_from_response(final_response.get("content", []))
            final_text_with_persona = self._prepend_persona_to_response(final_text)

            # Update conversation history
            self._update_conversation_history(
                user_input, assistant_message, tool_results, final_response["content"]
            )
            final_text = self._extract_text_from_response(final_text_with_persona)

            # Handle storage and observability
            self._finalize_conversation(user_input, final_text_with_persona)

            return final_text_with_persona

        except Exception as e:
            logging.error(f"Error processing message: {e}", exc_info=True)
            self._update_observability_with_error(str(e))
            return "I apologize, but I encountered an error. Please try again."

    def _handle_text_response(
        self, assistant_message: list[dict], user_input: str, text_parts: list[str]
    ) -> str:
        """Handle direct text response when no tools were used"""
        try:
            response_text = (
                " ".join(text_parts)
                if text_parts
                else self._extract_text_from_response(assistant_message)
            )
            response_text_with_persona = self._prepend_persona_to_response(response_text)

            # Don't update conversation history if this is an error message
            if not response_text.startswith("❌ Error communicating with Claude"):
                # Update conversation history only for successful responses
                self.llm.conversation_history.append({"role": "user", "content": user_input})
                self.llm.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )
            else:
                # Clean up conversation history when API errors occur
                self._cleanup_conversation_on_error()

            # Handle storage and observability
            self._finalize_conversation(user_input, response_text_with_persona)

            return response_text_with_persona

        except Exception as e:
            error_msg = f"Error handling text response: {str(e)}"
            logging.error(error_msg)
            self._update_observability_with_error(error_msg)
            return f"❌ {error_msg}"

    def _build_tool_conversation(
        self,
        messages: list[dict],
        assistant_message: list[dict],
        tool_results: list[dict],
    ) -> list[dict]:
        """Build conversation with tool results for final LLM call"""
        conversation = messages.copy()
        conversation.append({"role": "assistant", "content": assistant_message})

        # Format and add tool results
        formatted_results = self._format_tool_results(tool_results)
        conversation.append({"role": "user", "content": formatted_results})

        return self._sanitize_conversation(conversation)

    def _format_tool_results(self, tool_results: list[dict]) -> list[dict]:
        """Format tool results for Claude API"""
        formatted = []
        for result in tool_results:
            if isinstance(result, dict) and result.get("type") == "tool_result":
                formatted.append(result)
            else:
                logging.warning(f"Invalid tool result format: {result}")
        return formatted

    def _sanitize_conversation(self, messages: list[dict]) -> list[dict]:
        """Sanitize conversation messages for Claude API"""
        sanitized = []
        for i, message in enumerate(messages):
            if self._is_valid_message(message):
                sanitized.append({"role": message["role"], "content": message["content"]})
            else:
                logging.warning(f"Skipping invalid message at index {i}")
        return sanitized

    def _is_valid_message(self, message: dict) -> bool:
        """Validate message format"""
        if not isinstance(message, dict):
            return False
        if not all(key in message for key in ["role", "content"]):
            return False
        if message["role"] not in ["user", "assistant", "system"]:
            return False
        return True

    def _extract_text_from_response(self, content: list[dict]) -> str:
        """Extract text content from Claude response"""
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return "".join(text_parts)

    def _update_conversation_history(
        self,
        user_input: str,
        assistant_message: list[dict],
        tool_results: list[dict],
        final_content: list[dict],
    ) -> None:
        """Update conversation history with all parts of tool interaction"""
        formatted_results = self._format_tool_results(tool_results)

        # Prepend persona to the final assistant message before storing it
        final_content_with_persona = self._prepend_persona_to_content(final_content)

        self.llm.conversation_history.extend(
            [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": formatted_results},
                {"role": "assistant", "content": final_content_with_persona},
            ]
        )

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

    def _create_error_response(self, user_input: str, error_msg: str) -> str:
        """Create a formatted error response."""
        response = f"❌ Error processing request: {error_msg}"
        try:
            self._finalize_conversation(user_input, response)
        except Exception as e:
            logging.warning(f"Failed to finalize error conversation: {e}")
        return response

    def _update_history_and_finalize(
        self, user_input: str, response_text: str, assistant_message: list[dict]
    ):
        """Update conversation history and finalize the conversation."""
        try:
            # Update conversation history
            self.llm.conversation_history.extend(
                [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": assistant_message},
                ]
            )

            # Finalize conversation
            self._finalize_conversation(user_input, response_text)
        except Exception as e:
            logging.error(f"Error updating history and finalizing: {e}")

    def clear_history(self):
        """Clears the conversation history."""
        self.llm.clear_history()

    @property
    def conversation_length(self) -> int:
        """Returns the number of messages in the conversation history."""
        return len(self.llm.conversation_history)
