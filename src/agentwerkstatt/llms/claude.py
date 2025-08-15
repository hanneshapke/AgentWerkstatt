import os

from .api_client import ApiClient
from .base import BaseLLM


class ClaudeLLM(BaseLLM):
    """A client for interacting with the Anthropic Claude LLM."""

    def __init__(self, persona: str, model_name: str, tools: dict, observability_service=None):
        super().__init__(model_name, tools, persona, observability_service)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self._validate_api_key("ANTHROPIC_API_KEY")
        self.api_client = ApiClient(
            base_url="https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )

    def set_persona(self, persona: str):
        """Set the persona for the LLM"""
        self.persona = persona

    @property
    def system_prompt(self) -> str:
        """Get the system prompt"""
        return self._format_system_prompt()

    def make_api_request(self, messages: list[dict] = None) -> dict:
        """Make a request to the Claude API"""
        if not messages:
            return {"error": "No messages provided."}

        payload = self._build_payload(messages)
        llm_span = self.observability_service.observe_llm_call(
            model_name=self.model_name, messages=messages
        )

        response_data = self.api_client.post(payload)

        self.observability_service.update_llm_observation(llm_span, response_data)
        return response_data

    def query(self, prompt: str, context: str) -> str:
        """
        Sends a query to the language model and returns the response.
        """
        messages = [{"role": "user", "content": f"{context}\n\n{prompt}"}]
        response = self.make_api_request(messages)
        if "error" in response:
            return f"Error: {response['error']}"
        return response.get("content", [])[0].get("text", "")

    def get_info(self) -> dict:
        """
        Returns information about the model.
        """
        return {"model": self.model_name}

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
