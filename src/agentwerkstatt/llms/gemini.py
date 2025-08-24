"""Factory function for creating a Gemini LLM."""

import os
from typing import Any

from .generic_llm import GenericLLM


def create_gemini_llm(
    model_name: str,
    persona: str = "",
    tools: list[Any] = None,
    observability_service: Any = None,
    **kwargs: dict[str, Any],
) -> GenericLLM:
    """
    Factory function to create a Gemini LLM instance.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("'GEMINI_API_KEY' environment variable is required but not set.")

    api_base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    return GenericLLM(
        model_name=model_name,
        api_base_url=api_base_url,
        headers=headers,
        persona=persona,
        tools=tools,
        observability_service=observability_service,
    )
