"""Generic LLM implementation."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from .api_client import ApiClient
from .base import BaseLLM

if TYPE_CHECKING:
    from ..tools.schemas import ToolSchema


class GenericLLM(BaseLLM):
    """
    A generic LLM client that can be configured to work with various LLM APIs
    that follow a similar request/response structure.
    """

    def __init__(
        self,
        model_name: str,
        api_base_url: str,
        headers: dict[str, str],
        persona: str = "",
        tools: list[Any] = None,
        observability_service: Any = None,
    ):
        super().__init__(model_name, tools, persona, observability_service)
        self.api_client = ApiClient(base_url=api_base_url, headers=headers)

    def set_persona(self, persona: str):
        """Set the persona for the LLM."""
        self.persona = persona

    def make_api_request(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Makes a raw API request to the LLM."""
        payload = self._build_payload(messages)

        llm_span = None
        if self.observability_service:
            llm_span = self.observability_service.observe_llm_call(
                model_name=self.model_name, messages=messages
            )

        response_data = self.api_client.post(payload)

        if self.observability_service:
            self.observability_service.update_llm_observation(llm_span, response_data)

        return response_data

    def process_request(
        self,
        messages: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Processes a list of messages, sends them to the LLM API,
        and returns the conversation and assistant's response.
        """
        if not messages:
            return [], [{"type": "text", "text": "No messages to process."}]

        response = self.make_api_request(messages)

        if "error" in response:
            error_content = [{"type": "text", "text": f"Error: {response['error']}"}]
            return messages, error_content

        assistant_content = response.get("content", [])
        return messages, assistant_content

    def query(self, prompt: str, context: str = "") -> str:
        """Sends a query to the language model and returns the response."""
        messages = [{"role": "user", "content": f"{context}\n\n{prompt}"}]
        response = self.make_api_request(messages)
        if "error" in response:
            return f"Error: {response['error']}"

        content = response.get("content", [])
        if content and isinstance(content, list) and "text" in content[0]:
            return content[0].get("text", "")
        return str(content)

    def get_info(self) -> dict[str, str]:
        """Returns information about the model."""
        return {"model": self.model_name}

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        """Returns the JSON schema for each registered tool."""
        return [self._convert_to_openai_schema(tool.get_schema()) for tool in self.tools]

    def _convert_to_openai_schema(self, schema: ToolSchema) -> dict[str, Any]:
        """Converts the generic tool schema to the OpenAI format."""
        return {
            "type": "function",
            "function": {
                "name": schema.name,
                "description": schema.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        name: {
                            "type": prop.type,
                            "description": prop.description,
                        }
                        for name, prop in schema.input_schema.properties.items()
                    },
                    "required": schema.input_schema.required,
                },
            },
        }

    def _build_payload(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Constructs the payload for the API request."""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 4096,
            "system": self.persona,
        }
        tool_schemas = self._get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas
        return payload
