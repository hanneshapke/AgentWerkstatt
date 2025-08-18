import json

from absl import logging

from ..interfaces import (
    ObservabilityServiceProtocol,
    ToolExecutorProtocol,
    ToolResult,
)
from ..tools.discovery import ToolRegistry


class ToolExecutor(ToolExecutorProtocol):
    """Service for executing tool calls from an LLM."""

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
            tool_results.append(result.to_dict())

        return tool_results, text_parts

    def _execute_single_tool_call(self, tool_block: dict) -> ToolResult:
        """Executes a single tool call and returns a ToolResult."""
        logging.warning(f"Executing tool block: {tool_block}")
        tool_id = tool_block.get("id")
        tool_name = tool_block.get("name")
        tool_input = tool_block.get("input", {})

        if not all([tool_id, tool_name]):
            logging.error(f"Skipping malformed tool block: {tool_block}")
            return ToolResult(tool_use_id="", content="Malformed tool block", is_error=True)

        logging.warning(f"Executing tool '{tool_name}' (ID: {tool_id}) with input: {tool_input}")

        print(f"🛠️ Calling tool: {tool_name}")
        tool_span = self.observability_service.observe_tool_execution(tool_name, tool_input)

        try:
            tool = self.tool_registry.get_tool_by_name(tool_name)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found.")

            if not isinstance(tool_input, dict):
                raise TypeError(
                    f"Tool input for '{tool_name}' must be a dictionary, not {type(tool_input).__name__}."
                )

            result_content = tool.execute(**tool_input)

            if isinstance(result_content, dict | list):
                result_content = json.dumps(result_content, ensure_ascii=False)
            else:
                result_content = str(result_content)

            result = ToolResult(tool_use_id=tool_id, content=result_content)
            self.observability_service.update_tool_observation(tool_span, result.to_dict())
            return result

        except Exception as e:
            logging.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            error_content = f"Error in tool '{tool_name}': {e}"
            result = ToolResult(tool_use_id=tool_id, content=error_content, is_error=True)
            self.observability_service.update_tool_observation(tool_span, result.to_dict())
            return result
