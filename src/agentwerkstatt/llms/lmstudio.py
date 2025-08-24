"""Factory function for creating an LM Studio LLM."""

import os
from typing import Any

from .generic_llm import GenericLLM


def create_lmstudio_llm(
    model_name: str,
    tools: list[Any] = None,
    observability_service: Any = None,
    **kwargs: dict[str, Any],
) -> GenericLLM:
    """
    Factory function to create an LM Studio LLM instance.
    """
    api_base_url = os.getenv("LMSTUDIO_API_BASE_URL", "http://localhost:1234/v1/chat/completions")
    headers = {"Content-Type": "application/json"}

    return GenericLLM(
        model_name=model_name,
        api_base_url=api_base_url,
        api_headers=headers,
        tools=tools,
        observability_service=observability_service,
    )
