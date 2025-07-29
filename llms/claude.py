import os

import httpx
from absl import logging

from .base import BaseLLM


class ClaudeLLM(BaseLLM):
    """Claude LLM"""

    def __init__(
        self, agent_objective: str, model_name: str, tools: dict, observability_service=None
    ):
        super().__init__(model_name, tools, agent_objective, observability_service)

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        self._validate_api_key("ANTHROPIC_API_KEY")

    @property
    def system_prompt(self) -> str:
        """Get the system prompt"""
        _system_prompt = self._format_system_prompt()
        logging.debug(f"System prompt: {_system_prompt}")
        return _system_prompt

    def make_api_request(self, messages: list[dict] = None) -> dict:
        """Make a request to the Claude API"""

        # Start observing this LLM call
        llm_span = None
        if self.observability_service:
            llm_span = self.observability_service.observe_llm_call(
                model_name=self.model_name,
                messages=messages,
                metadata={
                    "max_tokens": 2000,
                    "num_tools": len(self.tools) if self.tools else 0,
                    "system_prompt_length": len(self.system_prompt),
                },
            )

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 2000,
            "system": self.system_prompt,
        }

        tool_schemas = self._get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas

        logging.debug(f"Making API request with payload: {payload}")
        logging.debug(f"Headers: {headers}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response_data = response.json()
                logging.debug(f"Response: {response_data}")
                response.raise_for_status()

                # Update observability with response data
                if llm_span and "usage" in response_data:
                    usage = response_data.get("usage", {})
                    self.observability_service.update_llm_observation(
                        llm_span=llm_span,
                        output=response_data.get("content", []),
                        usage={
                            "input_tokens": usage.get("input_tokens", 0),
                            "output_tokens": usage.get("output_tokens", 0),
                        },
                    )
                elif llm_span:
                    self.observability_service.update_llm_observation(
                        llm_span=llm_span, output=response_data.get("content", [])
                    )

                return response_data
        except httpx.HTTPError as e:
            error_response = {"error": f"API request failed: {str(e)}"}
            if llm_span:
                self.observability_service.update_llm_observation(
                    llm_span=llm_span, output=error_response
                )
            return error_response
        except Exception as e:
            error_response = {"error": f"Unexpected error: {str(e)}"}
            if llm_span:
                self.observability_service.update_llm_observation(
                    llm_span=llm_span, output=error_response
                )
            return error_response

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list]:
        """
        Process user request using Claude API

        Args:
            messages: List of conversation messages

        Returns:
            Tuple of (updated_messages, assistant_message_content)
        """

        # Make initial API request
        logging.debug(f"Making API request with {len(messages)} messages")
        logging.debug(f"Last 2 messages: {messages[-2:] if len(messages) >= 2 else messages}")
        response = self.make_api_request(messages)

        if "error" in response:
            # Return error as assistant message
            error_message = [
                {"type": "text", "text": f"❌ Error communicating with Claude: {response['error']}"}
            ]
            return messages, error_message

        # Process the response
        assistant_message = response.get("content", [])

        return messages, assistant_message
