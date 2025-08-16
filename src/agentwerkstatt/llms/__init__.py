"""LLM clients for the AgentWerkstatt."""
from .base import BaseLLM
from .claude import create_claude_llm
from .lmstudio import create_lmstudio_llm
from .mock import MockLLM
from .ollama import create_ollama_llm

__all__ = [
    "BaseLLM",
    "create_claude_llm",
    "create_lmstudio_llm",
    "create_ollama_llm",
    "MockLLM",
]
