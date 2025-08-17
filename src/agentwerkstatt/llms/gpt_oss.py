"""Factory function for creating a GPT-OSS LLM with schema conversion."""

import os
from typing import Any

from .generic_llm import GenericLLM


class GptOssLLM(GenericLLM):
    """
    GPT-OSS LLM that converts Claude native format to OpenAI function schemas.
    """

    def _convert_claude_schema_to_openai(self, claude_schema: dict[str, Any]) -> dict[str, Any]:
        """
        Converts Claude native tool format to OpenAI function schema format.

        Args:
            claude_schema: Schema in Claude native format with 'type': 'function'

        Returns:
            Schema in OpenAI function format with 'function'
        """
        if claude_schema.get("type") == "function" and "function" in claude_schema:
            function_def = claude_schema["function"]
            return {
                "name": function_def["name"],
                "description": function_def["description"],
                "input_schema": function_def["parameters"],
            }
        elif "input_schema" in claude_schema:
            # Already in OpenAI format
            return claude_schema
        else:
            # Handle mixed format - assume it's already OpenAI format if no 'type': 'function'
            return claude_schema

    def _get_tool_schemas(self) -> list[dict]:
        """
        Returns the JSON schema for each registered tool, converting from Claude format to OpenAI format.
        """
        raw_schemas = [tool.get_schema() for tool in self.tools]
        converted_schemas = []

        for schema in raw_schemas:
            converted_schema = self._convert_claude_schema_to_openai(schema)
            converted_schemas.append(converted_schema)

        return converted_schemas


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
    api_base_url = os.getenv("GPT_OSS_API_BASE_URL", "http://localhost:11434/v1/chat/completions")
    api_key = os.getenv("GPT_OSS_API_KEY", "")

    headers = {
        "Content-Type": "application/json",
    }

    # Add API key to headers if provided
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    return GptOssLLM(
        model_name=model_name,
        api_base_url=api_base_url,
        headers=headers,
        persona=persona,
        tools=tools,
        observability_service=observability_service,
    )
