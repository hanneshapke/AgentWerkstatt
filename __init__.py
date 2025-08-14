"""
AgentWerkstatt - A minimalistic agentic framework

This package provides a simple framework for building AI agents with tool capabilities,
memory, and observability features.
"""

from ._version import __version__
from .config import AgentConfig
from .main import Agent

__all__ = [
    "Agent",
    "AgentConfig",
    "__version__",
]

# Package metadata
__author__ = "Hannes Hapke"
