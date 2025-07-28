"""
AgentWerkstatt - A minimalistic agentic framework

This package provides a simple framework for building AI agents with tool capabilities,
memory, and observability features.
"""

from .agent import Agent
from .config import AgentConfig, ConfigManager, ConfigValidator

__all__ = [
    "Agent",
    "AgentConfig",
    "ConfigManager",
    "ConfigValidator",
]

# Package metadata
__version__ = "0.1.0"
__author__ = "Hannes Hapke"
