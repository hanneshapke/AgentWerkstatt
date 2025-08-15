from ..interfaces import ToolExecutorProtocol


class ToolInteractionHandler:
    """Handles the logic for executing tools and processing their results."""

    def __init__(self, tool_executor: ToolExecutorProtocol):
        self.tool_executor = tool_executor

    def handle_tool_calls(self, assistant_message_content: list) -> tuple[list[dict], list[str]]:
        """
        Executes tool calls and returns the results.
        """
        return self.tool_executor.execute_tool_calls(assistant_message_content)
