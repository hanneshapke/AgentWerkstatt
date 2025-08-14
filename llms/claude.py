import os
import httpx
from absl import logging
from .base import BaseLLM

class ClaudeLLM(BaseLLM):
    """A client for interacting with the Anthropic Claude LLM."""

    def __init__(self, persona: str, model_name: str, tools: dict, observability_service=None):
        super().__init__(model_name, tools, persona, observability_service)
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self._validate_api_key("ANTHROPIC_API_KEY")

    def make_api_request(self, messages: list[dict]) -> dict:
        """
        Makes a request to the Claude API with the given messages and returns the response.
        """
        if not messages:
            return {"error": "No messages provided."}

        payload = self._build_payload(messages)
        llm_span = self.observability_service.observe_llm_call(
            model_name=self.model_name, messages=messages
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
                response_data = response.json()
                
                self.observability_service.update_llm_observation(llm_span, response_data)
                return response_data

        except httpx.HTTPStatusError as e:
            error_details = e.response.json().get("error", {})
            error_message = error_details.get("message", e.response.text)
            logging.error(f"Claude API Error: {error_message}", exc_info=True)
            error_response = {"error": error_message}
            self.observability_service.update_llm_observation(llm_span, error_response)
            return error_response
        except httpx.RequestError as e:
            logging.error(f"Network error calling Claude API: {e}", exc_info=True)
            error_response = {"error": f"Network error: {e}"}
            self.observability_service.update_llm_observation(llm_span, error_response)
            return error_response

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Processes a list of messages, sends them to the Claude API, and returns the conversation and assistant's response.
        """
        if not messages:
            return [], [{"type": "text", "text": "No messages to process."}]

        response = self.make_api_request(messages)

        if "error" in response:
            error_content = [{"type": "text", "text": f"Error: {response['error']}"}]
            return messages, error_content

        assistant_content = response.get("content", [])
        return messages, assistant_content

    def _build_payload(self, messages: list[dict]) -> dict:
        """Constructs the payload for the Claude API request."""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 2000,
            "system": self.persona,
        }
        tool_schemas = self._get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas
        return payload