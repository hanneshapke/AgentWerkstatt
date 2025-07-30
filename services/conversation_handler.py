from collections.abc import Callable

from absl import logging

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
        """Default user ID provider"""
        return "default_user"

    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """Process a user message and return the agent's response"""
        try:
            # Get LLM response
            messages = self.llm.conversation_history + [{"role": "user", "content": enhanced_input}]
            messages, assistant_message = self.llm.process_request(messages)

            # Execute any tool calls
            tool_results, text_parts = self._execute_tools(assistant_message)

            # Generate final response
            if tool_results:
                return self._handle_tool_response(
                    messages, assistant_message, tool_results, user_input
                )
            else:
                return self._handle_text_response(assistant_message, user_input, text_parts)

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

            # Update conversation history
            self._update_conversation_history(
                user_input, assistant_message, tool_results, final_response["content"]
            )

            # Handle storage and observability
            self._finalize_conversation(user_input, final_text)

            return final_text

        except Exception as e:
            error_msg = f"Error handling tool response: {str(e)}"
            logging.error(error_msg)
            self._update_observability_with_error(error_msg)
            return f"❌ {error_msg}"

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
            self._finalize_conversation(user_input, response_text)

            return response_text

        except Exception as e:
            error_msg = f"Error handling text response: {str(e)}"
            logging.error(error_msg)
            self._update_observability_with_error(error_msg)
            return f"❌ {error_msg}"

    def _build_tool_conversation(
        self, messages: list[dict], assistant_message: list[dict], tool_results: list[dict]
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

        self.llm.conversation_history.extend(
            [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": formatted_results},
                {"role": "assistant", "content": final_content},
            ]
        )

    def _finalize_conversation(self, user_input: str, response_text: str) -> None:
        """Handle memory storage and observability"""
        # Store in memory
        self._store_in_memory(user_input, response_text)

        # Update observability
        self.observability_service.update_observation(response_text)
        self.observability_service.flush_traces()

    def _store_in_memory(self, user_input: str, response_text: str) -> None:
        """Store conversation in memory with error handling"""
        try:
            user_id = self.user_id_provider()
            self.memory_service.store_conversation(user_input, response_text, user_id)
            logging.debug("Memory storage completed")
        except Exception as e:
            logging.warning(f"Failed to store in memory: {e}")

    def _update_observability_with_error(self, error_msg: str) -> None:
        """Update observability with error information"""
        try:
            self.observability_service.update_observation({"error": error_msg})
            self.observability_service.flush_traces()
        except Exception as e:
            logging.warning(f"Failed to update observability: {e}")

    def _cleanup_conversation_on_error(self) -> None:
        """Clean up conversation history when API errors occur to prevent corruption"""
        try:
            # Find the last assistant message with unmatched tool_use blocks
            for i in range(len(self.llm.conversation_history) - 1, -1, -1):
                message = self.llm.conversation_history[i]
                if (message.get("role") == "assistant" and
                    isinstance(message.get("content"), list) and
                    any(block.get("type") == "tool_use" for block in message["content"])):

                    # Check if there's a corresponding tool_result in the next message
                    if (i + 1 < len(self.llm.conversation_history) and
                        self.llm.conversation_history[i + 1].get("role") == "user"):
                        next_content = self.llm.conversation_history[i + 1].get("content", [])
                        if isinstance(next_content, list) and any(block.get("type") == "tool_result" for block in next_content):
                            continue  # This tool_use has results, keep looking

                    # Found unmatched tool_use - remove from this point
                    logging.warning(f"Cleaning up conversation history from message {i} due to unmatched tool_use")
                    self.llm.conversation_history = self.llm.conversation_history[:i]
                    break

        except Exception as e:
            logging.error(f"Error cleaning conversation history: {e}")
            # Fallback: keep only the first message (user input)
            if self.llm.conversation_history:
                self.llm.conversation_history = self.llm.conversation_history[:1]

    def _create_error_response(self, user_input: str, error: str) -> str:
        """Create fallback response for critical errors"""
        fallback_message = "I apologize, but I encountered a system error while processing your request. Please try again later."
        logging.error(f"Critical error for input '{user_input}': {error}")

        self._update_observability_with_error(error)
        return fallback_message

    def enhance_input_with_memory(self, user_input: str) -> str:
        """Enhance user input with relevant memories"""
        try:
            user_id = self.user_id_provider()
            memory_context = self.memory_service.retrieve_memories(user_input, user_id)

            if memory_context:
                return f"{memory_context}\nUser query: {user_input}"
            return user_input
        except Exception as e:
            logging.warning(f"Failed to enhance input with memory: {e}")
            return user_input

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.llm.clear_history()

    @property
    def conversation_length(self) -> int:
        """Get current conversation length"""
        return len(self.llm.conversation_history)
