"""
AgentWerkstatt - A minimalistic agentic framework

This package provides a simple framework for building AI agents with tool capabilities,
memory, and observability features.
"""

try:
    from importlib.metadata import version

    __version__ = version("agentwerkstatt")
except Exception:
    # Fallback for development/testing
    __version__ = "0.1.0-dev"

# Import classes when used as a package
try:
    from config import AgentConfig
    from main import Agent

    __all__ = [
        "Agent",
        "AgentConfig",
        "__version__",
    ]
except ImportError:
    # During testing, these imports might fail
    __all__ = ["__version__"]

# Package metadata
__author__ = "Hannes Hapke"
