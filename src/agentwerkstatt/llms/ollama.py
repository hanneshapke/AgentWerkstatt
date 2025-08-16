"""Factory function for creating an Ollama LLM."""

import os
from typing import Any

from .generic_llm import GenericLLM


def create_ollama_llm(
    model_name: str,
    persona: str = "",
    tools: list[Any] = None,
    observability_service: Any = None,
    **kwargs: dict[str, Any],
) -> GenericLLM:
    """
    Factory function to create an Ollama LLM instance.
    """
    api_base_url = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434/api/chat")
    headers = {"Content-Type": "application/json"}

    return GenericLLM(
        model_name=model_name,
        api_base_url=api_base_url,
        api_headers=headers,
        persona=persona,
        tools=tools,
        observability_service=observability_service,
    )
