"""Factory function for creating a Claude LLM."""

import os
from typing import Any

from .generic_llm import GenericLLM


def create_claude_llm(
    model_name: str,
    persona: str = "",
    tools: list[Any] = None,
    observability_service: Any = None,
    **kwargs: dict[str, Any],
) -> GenericLLM:
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

    return GenericLLM(
        model_name=model_name,
        api_base_url="https://api.anthropic.com/v1/messages",
        headers=headers,
        persona=persona,
        tools=tools,
        observability_service=observability_service,
    )
