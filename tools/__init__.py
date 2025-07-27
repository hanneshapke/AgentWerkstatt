#!/usr/bin/env python3
"""
Tools package for AgentWerkstatt
Contains base tool class and all tool implementations
"""

from .discovery import ToolRegistry
from .websearch import TavilySearchTool

__all__ = ["TavilySearchTool", "ToolRegistry"]
