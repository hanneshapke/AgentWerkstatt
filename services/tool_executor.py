import json
from typing import Any

from absl import logging

from interfaces import ObservabilityServiceProtocol
from tools.discovery import ToolRegistry


class ToolExecutor:
    """Service for executing tool calls from an LLM."""

    def __init__(
        self, tool_registry: ToolRegistry, observability_service: ObservabilityServiceProtocol
    ):
        self.tool_registry = tool_registry
        self.observability_service = observability_service

    def execute_tool_calls(self, assistant_message_content: list) -> tuple[list[dict], list[str]]:
        """
        Parses an assistant's message content, executes any tool calls, and returns the results.
        """
        tool_results = []
        text_parts = []

        tool_use_blocks = [
            block for block in assistant_message_content if block.get("type") == "tool_use"
        ]

        for block in assistant_message_content:
            if block.get("type") == "text":
                text_parts.append(block["text"])

        if not tool_use_blocks:
            return [], text_parts

        for tool_block in tool_use_blocks:
            result = self._execute_single_tool_call(tool_block)
            tool_results.append(result)

        return tool_results, text_parts

    def _execute_single_tool_call(self, tool_block: dict) -> dict:
        """Executes a single tool call and returns a formatted result dictionary."""
        tool_id = tool_block.get("id")
        tool_name = tool_block.get("name")
        tool_input = tool_block.get("input", {})

        if not all([tool_id, tool_name]):
            logging.error(f"Skipping malformed tool block: {tool_block}")
            return {}

        logging.debug(f"Executing tool '{tool_name}' (ID: {tool_id}) with input: {tool_input}")

        tool_span = self.observability_service.observe_tool_execution(tool_name, tool_input)

        try:
            tool = self.tool_registry.get_tool_by_name(tool_name)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found.")

            # Ensure input is a dictionary
            if not isinstance(tool_input, dict):
                raise TypeError(
                    f"Tool input for '{tool_name}' must be a dictionary, not {type(tool_input).__name__}."
                )

            result_content = tool.execute(**tool_input)

            formatted_result = self._format_result(tool_id, result_content)
            self.observability_service.update_tool_observation(tool_span, formatted_result)
            return formatted_result

        except Exception as e:
            logging.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            error_content = f"Error in tool '{tool_name}': {e}"
            error_result = self._format_result(tool_id, error_content, is_error=True)
            self.observability_service.update_tool_observation(tool_span, error_result)
            return error_result

    def _format_result(self, tool_id: str, content: Any, is_error: bool = False) -> dict:
        """Formats the tool execution result into the required dictionary structure."""
        try:
            if isinstance(content, dict | list):
                content_str = json.dumps(content, ensure_ascii=False)
            else:
                content_str = str(content)
        except (TypeError, json.JSONDecodeError) as e:
            logging.error(f"Failed to serialize tool content: {e}")
            content_str = (
                f"Error: Could not serialize tool output of type {type(content).__name__}."
            )
            is_error = True

        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": content_str,
            "is_error": is_error,
        }
