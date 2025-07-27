# functions that discover tools listed in the tools folder

import importlib
import inspect
import os

from absl import logging

from .base import BaseTool


class ToolRegistry:
    def __init__(self, tools: list[BaseTool] = None, tools_dir: str = None):
        self.tools_dir = tools_dir or os.path.dirname(__file__)
        self.files_to_skip = ("__init__.py", "base.py", "discovery.py")
        self._tools = tools

    @property
    def tools(self) -> list[BaseTool]:
        """Lazy load tools when first accessed"""
        if self._tools is None and self.tools_dir is None:
            raise ValueError("Either tools or tools_dir must be provided")
        elif self._tools is None and self.tools_dir is not None:
            self._tools = self._discover_tools()
        return self._tools

    def get_tools(self) -> list[BaseTool]:
        """Get all tools"""
        return self.tools

    def _discover_tools(self) -> list[BaseTool]:
        """Discover all tool implementations in the tools directory"""
        tools = []

        for filename in os.listdir(self.tools_dir):
            if not filename.endswith(".py") or filename in self.files_to_skip:
                continue

            module_name = filename[:-3]  # Remove .py extension

            try:
                module = importlib.import_module(f".{module_name}", package="tools")

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseTool)
                        and obj is not BaseTool
                        and obj.__module__ == module.__name__
                    ):
                        try:
                            tool_instance = obj()
                            tools.append(tool_instance)
                            logging.debug(f"Discovered tool: {tool_instance.name}")
                        except Exception as e:
                            logging.error(f"Failed to instantiate tool {name}: {e}")

            except Exception as e:
                logging.error(f"Failed to import module {module_name}: {e}")

        logging.debug(f"Discovered {len(tools)} tools total")
        return tools

    def get_tool_schemas(self) -> list[dict]:
        """Get schemas for all discovered tools"""
        return [tool.get_schema() for tool in self.tools]

    def get_tool_by_name(self, name: str) -> BaseTool:
        """Get a specific tool by name"""
        for tool in self.tools:
            if tool.get_name() == name:
                return tool
        raise ValueError(
            f"Tool '{name}' not found. Available tools: {[t.name for t in self.tools]}"
        )
