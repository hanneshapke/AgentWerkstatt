import json
from typing import Any

from absl import logging

from ..interfaces import ObservabilityServiceProtocol
from ..tools.discovery import ToolRegistry


class ToolExecutor:
    """Service for executing tools with observability support"""

    def __init__(
        self, tool_registry: ToolRegistry, observability_service: ObservabilityServiceProtocol
    ):
        self.tool_registry = tool_registry
        self.observability_service = observability_service

    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call with observability tracking"""

        # Start observing tool execution - but don't complete it yet
        tool_span = None
        if self.observability_service:
            try:
                # Create a tool span that we can update with actual results
                tool_span = self.observability_service.observe_tool_execution(tool_name, tool_input)
                logging.debug(f"Started tool observation for {tool_name}")
            except Exception as e:
                logging.warning(f"Failed to start tool observation for {tool_name}: {e}")

        try:
            tool = self.tool_registry.get_tool_by_name(tool_name)
            if tool is None:
                error_msg = f"Unknown tool: {tool_name}"
                error_result = {"error": error_msg, "tool_name": tool_name}

                # Update observation with error
                if tool_span:
                    try:
                        self.observability_service.update_tool_observation(tool_span, error_result)
                    except Exception as e:
                        logging.warning(f"Failed to update tool observation with error: {e}")

                logging.error(error_msg)
                return error_result

            # Execute the actual tool
            result = tool.execute(**tool_input)

            # Update observation with successful result
            if tool_span:
                try:
                    self.observability_service.update_tool_observation(tool_span, result)
                except Exception as e:
                    logging.warning(f"Failed to update tool observation with result: {e}")

            logging.debug(f"Tool {tool_name} executed successfully")
            return result

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            error_result = {
                "error": error_msg,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "exception_type": type(e).__name__
            }

            # Update observation with error
            if tool_span:
                try:
                    self.observability_service.update_tool_observation(tool_span, error_result)
                except Exception as e:
                    logging.warning(f"Failed to update tool observation with error: {e}")

            logging.error(f"Tool {tool_name} execution failed: {e}")
            # Return error result instead of raising
            return error_result

    def _create_tool_result_message(self, tool_id: str, content: str, is_error: bool = False) -> dict:
        """Create a properly formatted tool result message"""
        result = {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": content
        }

        if is_error:
            result["is_error"] = True

        return result

    def _format_tool_result_content(self, result: dict[str, Any]) -> str:
        """Format tool result content for Claude"""
        if "error" in result:
            # Format error results clearly
            error_info = {
                "status": "error",
                "message": result["error"],
                "tool_name": result.get("tool_name", "unknown")
            }
            return json.dumps(error_info)
        else:
            # Format successful results
            try:
                return json.dumps(result)
            except (TypeError, ValueError) as e:
                # Fallback for non-serializable results
                logging.warning(f"Failed to serialize tool result: {e}")
                return json.dumps({"status": "success", "result": str(result)})

    def execute_tool_calls(self, assistant_message: list) -> tuple[list, list]:
        """
        Execute all tool calls from an assistant message

        Returns:
            tuple: (tool_results, final_response_parts)
        """
        tool_results = []
        final_response_parts = []
        tool_use_ids = set()  # Track tool_use IDs to ensure completeness

        # Debug: Log initial state
        logging.debug("=== Tool Execution Start ===")
        logging.debug(f"Assistant message blocks: {len(assistant_message)}")

        # First pass: identify all tool calls
        tool_calls_found = []
        for i, content_block in enumerate(assistant_message):
            block_type = content_block.get("type")
            logging.debug(f"Block {i}: type={block_type}")

            if block_type == "tool_use":
                tool_id = content_block.get("id")
                tool_name = content_block.get("name")
                tool_calls_found.append({"id": tool_id, "name": tool_name, "index": i})
                logging.debug(f"Found tool call {i}: {tool_name} (ID: {tool_id})")

        logging.debug(f"Total tool calls found: {len(tool_calls_found)}")
        logging.debug("=== Starting Tool Execution ===")

        for content_block in assistant_message:
            if content_block.get("type") == "text":
                final_response_parts.append(content_block["text"])
            elif content_block.get("type") == "tool_use":
                tool_name = content_block["name"]
                tool_input = content_block["input"]
                tool_id = content_block["id"]

                # Track this tool_use ID
                tool_use_ids.add(tool_id)

                logging.debug(f"Executing tool {tool_name} (ID: {tool_id})")
                logging.debug(f"Tool input: {tool_input}")

                try:
                    # Validate tool input before execution
                    if not isinstance(tool_input, dict):
                        raise ValueError(f"Tool input must be a dictionary, got {type(tool_input)}")

                    # Execute the tool
                    result = self.execute_tool(tool_name, tool_input)

                    # Check if the tool execution returned an error result
                    if isinstance(result, dict) and "error" in result:
                        # Tool execution failed, create error result for Claude
                        error_message = self._create_error_message(tool_name, result["error"])
                        error_result = {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": error_message,
                            "is_error": True,
                        }
                        tool_results.append(error_result)
                        logging.debug(f"Tool {tool_name} (ID: {tool_id}) returned error result: {result['error']}")
                        print(f"❌ Tool {tool_name} failed: {result['error']}")
                    else:
                        # Tool execution successful
                        if result is None:
                            raise ValueError("Tool returned None result")

                        # Create properly formatted tool result
                        tool_result = {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": self._format_tool_content(result),
                        }
                        tool_results.append(tool_result)
                        logging.debug(f"Tool {tool_name} (ID: {tool_id}) executed successfully")
                        print(f"✅ Tool {tool_name} completed successfully")

                except Exception as e:
                    # Handle unexpected exceptions during tool execution
                    logging.error(f"Tool {tool_name} (ID: {tool_id}) execution failed with exception: {e}")
                    print(f"❌ Error executing tool {tool_name}: {e}")

                    # Create a user-friendly error message for Claude
                    error_message = self._create_error_message(tool_name, str(e))
                    error_result = {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": error_message,
                        "is_error": True,
                    }
                    tool_results.append(error_result)
                    logging.debug(f"Tool {tool_name} (ID: {tool_id}) failed with error result")

        # Validate that we have results for all tool_use IDs
        result_ids = {result["tool_use_id"] for result in tool_results}
        missing_ids = tool_use_ids - result_ids

        logging.debug("=== Tool Execution Validation ===")
        logging.debug(f"Expected tool IDs: {tool_use_ids}")
        logging.debug(f"Actual result IDs: {result_ids}")
        logging.debug(f"Missing IDs: {missing_ids}")

        if missing_ids:
            logging.error(f"CRITICAL: Missing tool results for IDs: {missing_ids}")
            print(f"❌ CRITICAL: Missing tool results for IDs: {missing_ids}")

            # Add placeholder results for missing IDs to prevent conversation structure issues
            for missing_id in missing_ids:
                placeholder_result = {
                    "type": "tool_result",
                    "tool_use_id": missing_id,
                    "content": "Error: Tool execution failed to complete. No result available.",
                    "is_error": True,
                }
                tool_results.append(placeholder_result)
                logging.debug(f"Added placeholder result for missing ID: {missing_id}")

        logging.debug(f"Total tool results generated: {len(tool_results)} for {len(tool_use_ids)} tool calls")
        logging.debug("=== Tool Execution Complete ===")

        # Final validation: ensure every tool result has proper structure
        for i, result in enumerate(tool_results):
            if not isinstance(result, dict):
                logging.error(f"Tool result {i} is not a dict: {type(result)}")
            elif "tool_use_id" not in result:
                logging.error(f"Tool result {i} missing tool_use_id: {result}")
            elif "type" not in result or result["type"] != "tool_result":
                logging.error(f"Tool result {i} has incorrect type: {result.get('type')}")

        return tool_results, final_response_parts

    def _format_tool_content(self, result: any) -> str:
        """Format tool result content for Claude API"""
        try:
            if isinstance(result, str):
                return result
            elif isinstance(result, dict) or isinstance(result, list):
                return json.dumps(result, ensure_ascii=False)
            else:
                return str(result)
        except Exception as e:
            logging.error(f"Failed to format tool content: {e}")
            return f"Error formatting tool result: {str(e)}"

    def _create_error_message(self, tool_name: str, error: str) -> str:
        """Create a user-friendly error message for Claude"""
        if "API key" in error.lower() or "authentication" in error.lower():
            return f"The {tool_name} tool is not properly configured. Please check the API configuration."
        elif "timeout" in error.lower() or "connection" in error.lower():
            return f"The {tool_name} tool experienced a network issue. Please try again later."
        elif "rate limit" in error.lower():
            return f"The {tool_name} tool has reached its usage limit. Please try again later."
        else:
            return f"The {tool_name} tool encountered an error: {error}"
