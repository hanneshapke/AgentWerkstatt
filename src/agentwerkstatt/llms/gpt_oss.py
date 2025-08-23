"""Factory function for creating a GPT-OSS LLM with schema conversion."""

import os
from typing import Any

from .generic_llm import GenericLLM


class GptOssLLM(GenericLLM):
    """
    GPT-OSS LLM that converts Claude native format to OpenAI function schemas.
    """


def create_gpt_oss_llm(
    model_name: str,
    persona: str = "",
    tools: list[Any] = None,
    observability_service: Any = None,
    **kwargs: dict[str, Any],
) -> GptOssLLM:
    """
    Factory function to create a GPT-OSS LLM instance via Ollama.
    """
    api_base_url = os.getenv("GPT_OSS_API_BASE_URL", "http://localhost:1234/v1/chat/completions")
    api_key = os.getenv("GPT_OSS_API_KEY", "")

    headers = {
        "Content-Type": "application/json",
    }

    # Add API key to headers if provided
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # convert tools to openai schema
    if tools:
        tools = [tool.to_openai_schema() for tool in tools]

    return GptOssLLM(
        model_name=model_name,
        api_base_url=api_base_url,
        headers=headers,
        persona=persona,
        tools=tools,
        observability_service=observability_service,
    )
