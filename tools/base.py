#!/usr/bin/env python3
"""
Tools module for AgentWerkstatt
Contains base tool implementations for the agent
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all tools"""

    def __init__(self):
        self.name = self._get_name()
        self.description = self._get_description()

    @abstractmethod
    def _get_name(self) -> str:
        """Return the tool name"""
        pass

    def get_name(self) -> str:
        """Return the tool name"""
        return self.name.lower().replace(" ", "_").replace("-", "_")

    def get_function_name(self) -> str:
        """Return the dynamic function name"""
        return self.name.lower().replace(" ", "_").replace("-", "_") + "_tool"

    @abstractmethod
    def _get_description(self) -> str:
        """Return the tool description"""
        pass

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Return the tool schema for Claude"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool with given parameters"""
        pass


class Tool:
    """Simple tool class for testing and basic tool implementations"""

    def __init__(self, name: str, description: str, schema: dict):
        """Initialize tool with name, description and schema"""
        self.name = name
        self.description = description
        self.schema = schema

    def __call__(self, **kwargs):
        """Call the tool - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement __call__ method")
