from __future__ import annotations
import os
from typing import Any, TYPE_CHECKING

from agentwerkstatt.config import LLMConfig

from .generic_llm import GenericLLM

if TYPE_CHECKING:
    pass


class ClaudeLLM(GenericLLM):
    """A specialized LLM client for Claude models."""


def create_claude_llm(
    model_name: str,
    model_config: LLMConfig,
    tools: list[Any] = None,
    observability_service: Any = None,
    **kwargs: dict[str, Any],
) -> ClaudeLLM:
    """
    Factory function to create a Claude LLM instance.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("'ANTHROPIC_API_KEY' environment variable is required but not set.")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    return ClaudeLLM(
        model_name=model_name,
        model_config=model_config,
        api_base_url="https://api.anthropic.com/v1/messages",
        headers=headers,
        tools=tools,
        observability_service=observability_service,
    )
