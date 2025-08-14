import importlib
import inspect
import os

from absl import logging

from .base import BaseTool


class ToolRegistry:
    """A registry for discovering and managing agent tools."""

    def __init__(self, tools_dir: str):
        if not os.path.isdir(tools_dir):
            raise ValueError(f"Tools directory '{tools_dir}' does not exist.")
        self.tools_dir = tools_dir
        self._tools = self._discover_tools()
        self._tool_map = {tool.get_name(): tool for tool in self._tools}
        logging.info(f"Initialized ToolRegistry with {len(self._tools)} tools.")

    def _discover_tools(self) -> list[BaseTool]:
        """
        Dynamically discovers and instantiates tool classes from the specified directory.
        """
        tools = []
        files_to_skip = ("__init__.py", "base.py", "discovery.py")

        for filename in os.listdir(self.tools_dir):
            if not filename.endswith(".py") or filename in files_to_skip:
                continue

            module_name = f"agentwerkstatt.tools.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        tools.append(obj())
                        logging.debug(f"Discovered and instantiated tool: {obj.__name__}")
            except ImportError as e:
                logging.error(f"Failed to import tool module {module_name}: {e}")
            except Exception as e:
                logging.error(f"Error instantiating tool from {module_name}: {e}", exc_info=True)

        return tools

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all discovered tool instances."""
        return self._tools

    def get_tool_by_name(self, name: str) -> BaseTool | None:
        """
        Retrieves a tool instance by its name.
        Returns:
            The tool instance or None if not found.
        """
        return self._tool_map.get(name)

    def get_tool_schemas(self) -> list[dict]:
        """Returns the JSON schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools]
