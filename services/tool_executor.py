import json
from absl import logging
from typing import Any

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

        # Start observing tool execution
        self.observability_service.observe_tool_execution(tool_name, tool_input)

        try:
            tool = self.tool_registry.get_tool_by_name(tool_name)
            if tool is None:
                raise ValueError(f"Unknown tool: {tool_name}")

            result = tool.execute(**tool_input)

            # Update observation with successful result
            self.observability_service.update_observation(result)

            logging.debug(f"Tool {tool_name} executed successfully")
            return result

        except Exception as e:
            error_result = {"error": str(e)}

            # Update observation with error
            self.observability_service.update_observation(error_result)

            logging.error(f"Tool {tool_name} execution failed: {e}")
            raise

    def execute_tool_calls(self, assistant_message: list) -> tuple[list, list]:
        """
        Execute all tool calls from an assistant message

        Returns:
            tuple: (tool_results, final_response_parts)
        """
        tool_results = []
        final_response_parts = []

        for content_block in assistant_message:
            if content_block.get("type") == "text":
                final_response_parts.append(content_block["text"])
            elif content_block.get("type") == "tool_use":
                tool_name = content_block["name"]
                tool_input = content_block["input"]
                tool_id = content_block["id"]

                try:
                    # Execute the tool
                    result = self.execute_tool(tool_name, tool_input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result),
                        }
                    )
                except Exception as e:
                    print(f"❌ Error executing tool {tool_name}: {e}")
                    # Add error result instead of failing completely
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error: {str(e)}",
                        }
                    )

        return tool_results, final_response_parts
