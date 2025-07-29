from collections.abc import Callable
from absl import logging
from typing import Any, Union

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

    def _validate_message_format(self, message: dict) -> bool:
        """Validate that a message has the correct format for Claude API"""
        if not isinstance(message, dict):
            logging.error(f"Message is not a dict: {type(message)} - {message}")
            return False

        if "role" not in message:
            logging.error(f"Message missing 'role': {message}")
            return False

        if "content" not in message:
            logging.error(f"Message missing 'content': {message}")
            return False

        # Validate role
        if message["role"] not in ["user", "assistant", "system"]:
            logging.error(f"Invalid role '{message['role']}' in message: {message}")
            return False

        # Validate content format
        content = message["content"]
        if isinstance(content, str):
            # String content is valid
            return True
        elif isinstance(content, list):
            # List content should contain valid content blocks
            for block in content:
                if not isinstance(block, dict):
                    logging.error(f"Content block is not a dict: {type(block)} - {block}")
                    return False
                if "type" not in block:
                    logging.error(f"Content block missing 'type': {block}")
                    return False
        else:
            logging.error(f"Invalid content type: {type(content)} - {content}")
            return False

        return True

    def _sanitize_conversation(self, messages: list[dict]) -> list[dict]:
        """Sanitize conversation messages to ensure they're valid for Claude API"""
        sanitized_messages = []

        for i, message in enumerate(messages):
            if not self._validate_message_format(message):
                logging.warning(f"Skipping invalid message at index {i}: {message}")
                continue

            # Deep copy to avoid modifying original
            sanitized_message = {
                "role": message["role"],
                "content": message["content"]
            }

            # Ensure content is properly formatted
            if isinstance(sanitized_message["content"], str):
                # String content is fine as-is
                pass
            elif isinstance(sanitized_message["content"], list):
                # Validate each content block
                validated_content = []
                for block in sanitized_message["content"]:
                    if isinstance(block, dict) and "type" in block:
                        validated_content.append(block)
                    else:
                        logging.warning(f"Skipping invalid content block: {block}")

                sanitized_message["content"] = validated_content

            sanitized_messages.append(sanitized_message)

        return sanitized_messages

    def _format_tool_results_for_claude(self, tool_results: list[dict]) -> list[dict]:
        """Format tool results as proper content blocks for Claude"""
        content_blocks = []

        for tool_result in tool_results:
            # Ensure tool result has the expected structure
            if not isinstance(tool_result, dict):
                logging.warning(f"Invalid tool result format: {tool_result}")
                continue

            if tool_result.get("type") != "tool_result":
                logging.warning(f"Tool result missing or invalid type: {tool_result}")
                continue

            # Tool results should be properly formatted content blocks
            content_blocks.append(tool_result)

        return content_blocks

    def process_message(self, user_input: str, enhanced_input: str) -> str:
        """Process a user message and return the agent's response"""

        # Create message for LLM
        user_message = {"role": "user", "content": enhanced_input}
        messages = self.llm.conversation_history + [user_message]

        # Debug: Log conversation before making API call
        logging.debug("=== Conversation Before API Call ===")
        logging.debug(f"Conversation history length: {len(self.llm.conversation_history)}")
        logging.debug(f"Total messages to send: {len(messages)}")
        if len(messages) > 0:
            logging.debug(f"Last message in history: {messages[-1]}")
        logging.debug("=== End Pre-API Debug ===")

        try:
            messages, assistant_message = self.llm.process_request(messages)

            # Handle tool calls if present - isolate tool execution state
            tool_execution_successful = False
            tool_results = []
            final_response_parts = []

            try:
                tool_results, final_response_parts = self.tool_executor.execute_tool_calls(
                    assistant_message
                )
                tool_execution_successful = True
                logging.debug(f"Tool execution completed successfully. Results: {len(tool_results)}")
            except Exception as tool_error:
                logging.error(f"Critical error during tool execution: {tool_error}")
                # Continue with empty tool results to prevent conversation corruption
                tool_results = []
                final_response_parts = []

            if tool_results and tool_execution_successful:
                # Check if all tools failed
                all_tools_failed = all(
                    result.get("is_error", False) for result in tool_results
                )

                if all_tools_failed:
                    logging.warning("All tool executions failed, providing fallback response")
                    return self._create_tool_failure_fallback(user_input, tool_results, final_response_parts)

                # If there were tool calls, get final response from Claude
                return self._handle_tool_calls_response(
                    messages, assistant_message, tool_results, user_input
                )
            else:
                # No tool calls or tool execution failed, return the text response
                return self._handle_direct_response(assistant_message, user_input, final_response_parts)

        except Exception as e:
            logging.error(f"Critical error in message processing: {e}")
            return self._create_critical_error_fallback(user_input, str(e))

    def _handle_tool_calls_response(
        self,
        messages: list[dict],
        assistant_message: list[dict],
        tool_results: list[dict],
        original_user_input: str,
    ) -> str:
        """Handle response when tool calls were made"""

        try:
            # Debug: Log tool execution state before processing
            logging.debug("=== Tool Calls Response Debug ===")
            logging.debug(f"Number of tool results received: {len(tool_results)}")
            tool_use_ids_in_results = {result.get("tool_use_id") for result in tool_results if result.get("tool_use_id")}
            logging.debug(f"Tool use IDs in results: {tool_use_ids_in_results}")

            # Extract tool use IDs from assistant message for comparison
            tool_use_ids_in_message = set()
            for block in assistant_message:
                if block.get("type") == "tool_use" and block.get("id"):
                    tool_use_ids_in_message.add(block["id"])
            logging.debug(f"Tool use IDs in assistant message: {tool_use_ids_in_message}")

            # Check for missing tool results
            missing_tool_ids = tool_use_ids_in_message - tool_use_ids_in_results
            if missing_tool_ids:
                logging.error(f"CRITICAL: Missing tool results for IDs: {missing_tool_ids}")

            logging.debug("=== End Tool Calls Debug ===")

            # Add the assistant's message with tool calls
            messages = messages + [{"role": "assistant", "content": assistant_message}]

            # Format tool results properly for Claude
            formatted_tool_results = self._format_tool_results_for_claude(tool_results)

            # Add tool results as user message with proper content blocks
            messages = messages + [{"role": "user", "content": formatted_tool_results}]

            # Sanitize the complete conversation before final API call
            sanitized_messages = self._sanitize_conversation(messages)

            # Debug: Log the message structure being sent to Claude
            logging.debug("=== Tool Call Conversation Structure ===")
            logging.debug(f"Total sanitized messages: {len(sanitized_messages)}")
            for i, msg in enumerate(sanitized_messages[-3:]):  # Show last 3 messages
                logging.debug(f"Message {len(sanitized_messages) - 3 + i}: role={msg.get('role')}, content_type={type(msg.get('content'))}")
            logging.debug("=== End Tool Call Debug ===")

            # Get final response from Claude
            final_response = self.llm.make_api_request(sanitized_messages)

            if "error" in final_response:
                error_msg = f"Error getting final response: {final_response['error']}"
                logging.error(error_msg)
                return f"❌ {error_msg}"

            final_content = final_response.get("content", [])
            final_text = ""
            for block in final_content:
                if block.get("type") == "text":
                    final_text += block["text"]

            # Fix: Use consistent conversation history management - append instead of replace
            # This prevents loss of conversation state during tool execution
            self.llm.conversation_history.append({"role": "user", "content": original_user_input})
            self.llm.conversation_history.append({"role": "assistant", "content": assistant_message})
            self.llm.conversation_history.append({"role": "user", "content": formatted_tool_results})
            self.llm.conversation_history.append({"role": "assistant", "content": final_content})

            # Debug: Log final conversation state
            logging.debug("=== Final Conversation History ===")
            logging.debug(f"Conversation history length: {len(self.llm.conversation_history)}")
            logging.debug("=== End Final History Debug ===")

            # Store conversation in memory AFTER all tool execution is complete
            # This prevents memory service from interfering with tool execution flow
            try:
                user_id = self.user_id_provider()
                self.memory_service.store_conversation(original_user_input, final_text, user_id)
                logging.debug("Memory storage completed successfully")
            except Exception as memory_error:
                logging.warning(f"Failed to store conversation in memory: {memory_error}")
                # Don't fail the entire request if memory storage fails

            # Update observability with final output
            self.observability_service.update_observation(final_text)

            # Flush traces to ensure data is submitted to Langfuse
            self.observability_service.flush_traces()

            return final_text

        except Exception as e:
            error_msg = f"Error handling tool calls response: {str(e)}"
            logging.error(error_msg)

            # Update observability with error
            self.observability_service.update_observation({"error": error_msg})
            self.observability_service.flush_traces()

            return f"❌ {error_msg}"

    def _handle_direct_response(
        self,
        assistant_message: list[dict],
        original_user_input: str,
        final_response_parts: list[str],
    ) -> str:
        """Handle direct response when no tool calls were made"""

        try:
            # No tool calls, return the text response
            response_text = " ".join(final_response_parts)

            # Update conversation history (use original user_input for history, not enhanced)
            self.llm.conversation_history.append({"role": "user", "content": original_user_input})
            self.llm.conversation_history.append({"role": "assistant", "content": assistant_message})

            # Debug: Log conversation state for direct response
            logging.debug("=== Direct Response - Final History ===")
            logging.debug(f"Conversation history length: {len(self.llm.conversation_history)}")
            logging.debug("=== End Direct Response Debug ===")

            # Store conversation in memory AFTER conversation state is finalized
            # This prevents memory service from interfering with conversation flow
            try:
                user_id = self.user_id_provider()
                self.memory_service.store_conversation(original_user_input, response_text, user_id)
                logging.debug("Memory storage completed successfully")
            except Exception as memory_error:
                logging.warning(f"Failed to store conversation in memory: {memory_error}")
                # Don't fail the entire request if memory storage fails

            # Update observability with final output
            self.observability_service.update_observation(response_text)

            # Flush traces to ensure data is submitted to Langfuse
            self.observability_service.flush_traces()

            return response_text

        except Exception as e:
            error_msg = f"Error handling direct response: {str(e)}"
            logging.error(error_msg)

            # Update observability with error
            self.observability_service.update_observation({"error": error_msg})
            self.observability_service.flush_traces()

            return f"❌ {error_msg}"

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.llm.clear_history()

    def _validate_conversation_structure(self, messages: list[dict]) -> dict:
        """
        Validate conversation structure to ensure it's safe to send to Claude.

        Specifically checks that:
        1. Every tool_use has a corresponding tool_result
        2. Message roles are valid
        3. Content structure is proper

        Returns:
            dict: {"valid": bool, "error": str}
        """
        try:
            tool_use_ids = set()
            tool_result_ids = set()

            for i, message in enumerate(messages):
                # Validate message structure
                if not isinstance(message, dict):
                    return {"valid": False, "error": f"Message {i} is not a dictionary"}

                if "role" not in message:
                    return {"valid": False, "error": f"Message {i} missing 'role' field"}

                if "content" not in message:
                    return {"valid": False, "error": f"Message {i} missing 'content' field"}

                role = message["role"]
                content = message["content"]

                # Validate role
                if role not in ["user", "assistant", "system"]:
                    return {"valid": False, "error": f"Message {i} has invalid role: {role}"}

                # Check content structure for tool usage
                if isinstance(content, list):
                    for j, content_block in enumerate(content):
                        if not isinstance(content_block, dict):
                            return {"valid": False, "error": f"Message {i} content block {j} is not a dictionary"}

                        block_type = content_block.get("type")

                        if block_type == "tool_use":
                            tool_id = content_block.get("id")
                            if not tool_id:
                                return {"valid": False, "error": f"Message {i} tool_use block missing 'id'"}
                            tool_use_ids.add(tool_id)

                            # Validate tool_use structure
                            if "name" not in content_block:
                                return {"valid": False, "error": f"Message {i} tool_use block missing 'name'"}
                            if "input" not in content_block:
                                return {"valid": False, "error": f"Message {i} tool_use block missing 'input'"}

                        elif block_type == "tool_result":
                            tool_use_id = content_block.get("tool_use_id")
                            if not tool_use_id:
                                return {"valid": False, "error": f"Message {i} tool_result block missing 'tool_use_id'"}
                            tool_result_ids.add(tool_use_id)

                            # Validate tool_result structure
                            if "content" not in content_block:
                                return {"valid": False, "error": f"Message {i} tool_result block missing 'content'"}

            # Check that every tool_use has a corresponding tool_result
            missing_results = tool_use_ids - tool_result_ids
            if missing_results:
                return {"valid": False, "error": f"Missing tool_result blocks for tool_use IDs: {list(missing_results)}"}

            # Check for orphaned tool_results (results without corresponding tool_use)
            orphaned_results = tool_result_ids - tool_use_ids
            if orphaned_results:
                logging.warning(f"Found orphaned tool_result blocks for IDs: {list(orphaned_results)}")
                # This is a warning but not a blocking error

            return {"valid": True, "error": ""}

        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    @property
    def conversation_length(self) -> int:
        """Get current conversation length"""
        return len(self.llm.conversation_history)

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

    def _create_tool_failure_fallback(self, user_input: str, tool_results: list[dict], final_response_parts: list[str]) -> str:
        """Create a fallback response when all tools fail"""

        # Extract the text response if available
        text_response = " ".join(final_response_parts) if final_response_parts else ""

        # Create a helpful fallback message
        fallback_message = f"""I apologize, but I encountered issues with the tools needed to fully answer your question about "{user_input}".

The specific issues were:
"""

        # Add error details
        for i, result in enumerate(tool_results, 1):
            tool_content = result.get("content", "Unknown error")
            fallback_message += f"{i}. {tool_content}\n"

        # Add any text response if available
        if text_response:
            fallback_message += f"\nHowever, I can still provide this information: {text_response}"
        else:
            fallback_message += "\nPlease try your request again later, or rephrase your question if possible."

        # Update conversation history with fallback
        self.llm.conversation_history.append({"role": "user", "content": user_input})
        self.llm.conversation_history.append({"role": "assistant", "content": [{"type": "text", "text": fallback_message}]})

        # Store in memory
        user_id = self.user_id_provider()
        self.memory_service.store_conversation(user_input, fallback_message, user_id)

        # Update observability
        self.observability_service.update_observation(fallback_message)
        self.observability_service.flush_traces()

        return fallback_message

    def _create_critical_error_fallback(self, user_input: str, error: str) -> str:
        """Create a fallback response for critical system errors"""

        fallback_message = f"I apologize, but I encountered a system error while processing your request. Please try again later."

        logging.error(f"Critical error fallback for input '{user_input}': {error}")

        # Don't update conversation history for critical errors to avoid corrupting it

        # Update observability with error
        self.observability_service.update_observation({"error": error, "fallback_message": fallback_message})
        self.observability_service.flush_traces()

        return fallback_message
