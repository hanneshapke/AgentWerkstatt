"""Generic LLM implementation."""

from __future__ import annotations
import re
from absl import logging
from typing import Any

from ..config import LLMConfig
from .api_client import ApiClient
from .base import BaseLLM


class GenericLLM(BaseLLM):
    """
    A generic LLM client that can be configured to work with various LLM APIs
    that follow a similar request/response structure.
    """

    def __init__(
        self,
        model_name: str,
        model_config: LLMConfig,
        api_base_url: str,
        headers: dict[str, str],
        tools: list[Any] = None,
        observability_service: Any = None,
    ):
        super().__init__(model_name, tools, observability_service)
        self.api_client = ApiClient(base_url=api_base_url, headers=headers)
        self.max_tokens = model_config.max_tokens or 4096
        self.temperature = model_config.temperature or 0.7

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
            _content = content[0].get("text", "")
        else:
            _content = str(content)
        # get text between ```json and ```
        try:
            match = re.search(r"```json(.*)```", _content, re.DOTALL)
            if match:
                _content = match.group(1)
                return _content  # Return the JSON string, not parsed object
            else:
                return _content  # Return original content if no JSON block found
        except Exception as e:
            logging.warning(f"Error parsing LLM response: {e} with content: {_content}")
            return _content

    def get_info(self) -> dict[str, str]:
        """Returns information about the model."""
        return {"model": self.model_name}

    def _get_tool_schemas(self) -> list[dict[str, Any]]:
        """Returns the JSON schema for each registered tool."""
        return [tool.get_schema() for tool in self.tools]

    def _build_payload(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Constructs the payload for the API request."""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if self.tools:
            payload["tools"] = [tool.get_schema().to_claude_schema() for tool in self.tools]
        return payload
