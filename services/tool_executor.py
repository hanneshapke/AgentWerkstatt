import json
from typing import Any

from absl import logging

from ..interfaces import ObservabilityServiceProtocol
from ..tools.discovery import ToolRegistry


class ToolExecutor:
    """Service for executing tools with observability support"""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        observability_service: ObservabilityServiceProtocol,
        agent_instance=None,
    ):
        self.tool_registry = tool_registry
        self.observability_service = observability_service
        self.agent = agent_instance
        self._inject_agent_into_tools()

    def _inject_agent_into_tools(self):
        """Inject the agent instance into tools that require it."""
        if not self.agent:
            return
        for tool in self.tool_registry.get_tools():
            if hasattr(tool, "agent"):
                tool.agent = self.agent

    def execute_tool_calls(self, assistant_message: list) -> tuple[list, list]:
        """Execute all tool calls from an assistant message"""
        tool_results = []
        text_parts = []

        logging.debug(f"Processing {len(assistant_message)} content blocks")

        for block in assistant_message:
            if block.get("type") == "text":
                text_parts.append(block["text"])
            elif block.get("type") == "tool_use":
                result = self._execute_single_tool_call(block)
                tool_results.append(result)

        # Validate all tool calls have results
        self._validate_tool_results(assistant_message, tool_results)

        logging.debug(f"Completed {len(tool_results)} tool executions")
        return tool_results, text_parts

    def _execute_single_tool_call(self, tool_block: dict) -> dict:
        """Execute a single tool call and return formatted result"""
        tool_id = tool_block["id"]
        tool_name = tool_block["name"]
        tool_input = tool_block["input"]

        logging.debug(f"Executing {tool_name} (ID: {tool_id})")

        try:
            # Validate input
            if not isinstance(tool_input, dict):
                raise ValueError(f"Tool input must be a dictionary, got {type(tool_input)}")

            # Execute tool with observability
            result = self._execute_tool_with_observability(tool_name, tool_input)

            # Handle result
            if self._is_error_result(result):
                return self._create_error_tool_result(tool_id, tool_name, result["error"])
            else:
                return self._create_success_tool_result(tool_id, result)

        except Exception as e:
            logging.error(f"Tool {tool_name} execution failed: {e}")
            return self._create_error_tool_result(tool_id, tool_name, str(e))

    def _execute_tool_with_observability(self, tool_name: str, tool_input: dict) -> dict:
        """Execute tool with observability tracking"""
        # Start observation
        tool_span = self._start_tool_observation(tool_name, tool_input)

        try:
            # Get and execute tool
            tool = self.tool_registry.get_tool_by_name(tool_name)
            if tool is None:
                result = {"error": f"Unknown tool: {tool_name}", "tool_name": tool_name}
            else:
                result = tool.execute(**tool_input)

            # Update observation with result
            self._update_tool_observation(tool_span, result)
            return result

        except Exception as e:
            error_result = {
                "error": f"Tool execution failed: {str(e)}",
                "tool_name": tool_name,
                "exception_type": type(e).__name__,
            }
            self._update_tool_observation(tool_span, error_result)
            return error_result

    def _start_tool_observation(self, tool_name: str, tool_input: dict) -> Any:
        """Start tool observation, return span or None"""
        if not self.observability_service:
            return None
        try:
            return self.observability_service.observe_tool_execution(tool_name, tool_input)
        except Exception as e:
            logging.warning(f"Failed to start tool observation: {e}")
            return None

    def _update_tool_observation(self, tool_span: Any, result: dict) -> None:
        """Update tool observation with result"""
        if not tool_span or not self.observability_service:
            return
        try:
            self.observability_service.update_tool_observation(tool_span, result)
        except Exception as e:
            logging.warning(f"Failed to update tool observation: {e}")

    def _is_error_result(self, result: dict) -> bool:
        """Check if result indicates an error"""
        return isinstance(result, dict) and "error" in result

    def _create_success_tool_result(self, tool_id: str, result: Any) -> dict:
        """Create a successful tool result"""
        if result is None:
            raise ValueError("Tool returned None result")

        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": self._format_tool_content(result),
        }

    def _create_error_tool_result(self, tool_id: str, tool_name: str, error: str) -> dict:
        """Create an error tool result"""
        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": self._create_user_friendly_error(tool_name, error),
            "is_error": True,
        }

    def _format_tool_content(self, result: Any) -> str:
        """Format tool result content for Claude API"""
        try:
            if isinstance(result, str):
                return result
            elif isinstance(result, dict | list):
                return json.dumps(result, ensure_ascii=False)
            else:
                return str(result)
        except Exception as e:
            logging.error(f"Failed to format tool content: {e}")
            return f"Error formatting tool result: {str(e)}"

    def _create_user_friendly_error(self, tool_name: str, error: str) -> str:
        """Create a user-friendly error message"""
        error_lower = error.lower()

        if "api key" in error_lower or "authentication" in error_lower:
            return f"The {tool_name} tool is not properly configured. Please check the API configuration."
        elif "timeout" in error_lower or "connection" in error_lower:
            return f"The {tool_name} tool experienced a network issue. Please try again later."
        elif "rate limit" in error_lower:
            return f"The {tool_name} tool has reached its usage limit. Please try again later."
        else:
            return f"The {tool_name} tool encountered an error: {error}"

    def _validate_tool_results(self, assistant_message: list, tool_results: list) -> None:
        """Validate that all tool calls have corresponding results"""
        # Extract tool IDs from original message
        expected_ids = {
            block["id"] for block in assistant_message if block.get("type") == "tool_use"
        }

        # Extract tool IDs from results
        actual_ids = {result["tool_use_id"] for result in tool_results}

        # Check for missing results
        missing_ids = expected_ids - actual_ids
        if missing_ids:
            logging.error(f"Missing tool results for IDs: {missing_ids}")
            # Add placeholder results
            for missing_id in missing_ids:
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": missing_id,
                        "content": "Error: Tool execution failed to complete. No result available.",
                        "is_error": True,
                    }
                )

    # Legacy methods for backward compatibility (marked for removal)
    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Legacy method - use _execute_tool_with_observability instead"""
        logging.warning("execute_tool is deprecated, use _execute_tool_with_observability")
        return self._execute_tool_with_observability(tool_name, tool_input)
