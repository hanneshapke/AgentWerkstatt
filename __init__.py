"""
AgentWerkstatt - A minimalistic agentic framework

This package provides a simple framework for building AI agents with tool capabilities,
memory, and observability features.
"""

from ._version import __version__
from .agent import Agent
from .config import AgentConfig, ConfigManager, ConfigValidator

__all__ = [
    "Agent",
    "AgentConfig",
    "ConfigManager",
    "ConfigValidator",
    "__version__",
]

# Package metadata
__author__ = "Hannes Hapke"
