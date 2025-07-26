#!/usr/bin/env python3
"""
  Tools module for AgentWerkstatt
  Contains base tool implementations for the agent
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """Abstract base class for all tools"""

    def __init__(self):
        self.name = self._get_name()
        self.description = self._get_description()

    @abstractmethod
    def _get_name(self) -> str:
        """Return the tool name"""
        pass

    @abstractmethod
    def _get_description(self) -> str:
        """Return the tool description"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return the tool schema for Claude"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
