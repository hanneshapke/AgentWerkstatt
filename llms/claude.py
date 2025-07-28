import os

import httpx
from absl import logging

from .base import BaseLLM, observe


class ClaudeLLM(BaseLLM):
    """Claude LLM"""

    def __init__(self, agent_objective: str, model_name: str, tools: dict):
        super().__init__(model_name, tools, agent_objective)

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        self._validate_api_key("ANTHROPIC_API_KEY")

    @property
    def system_prompt(self) -> str:
        """Get the system prompt"""
        _system_prompt = self._format_system_prompt()
        logging.debug(f"System prompt: {_system_prompt}")
        return _system_prompt

    @observe(as_type="generation")
    def make_api_request(self, messages: list[dict] = None) -> dict:
        """Make a request to the Claude API"""

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

        # Update Langfuse context if available
        self._update_langfuse_observation(
            name="Claude API Call",
            model=self.model_name,
            input=messages,
            metadata={
                "max_tokens": 2000,
                "num_tools": len(self.tools) if self.tools else 0,
                "system_prompt_length": len(self.system_prompt),
            },
        )

        logging.debug(f"Making API request with payload: {payload}")
        logging.debug(f"Headers: {headers}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response_data = response.json()
                logging.debug(f"Response: {response_data}")
                response.raise_for_status()

                # Update Langfuse with response data
                if "usage" in response_data:
                    usage = response_data.get("usage", {})
                    self._update_langfuse_observation(
                        output=response_data.get("content", []),
                        usage_details={
                            "input": usage.get("input_tokens", 0),
                            "output": usage.get("output_tokens", 0),
                        },
                    )

                return response_data
        except httpx.HTTPError as e:
            error_response = {"error": f"API request failed: {str(e)}"}
            self._update_langfuse_observation(output=error_response, level="ERROR")
            return error_response
        except Exception as e:
            error_response = {"error": f"Unexpected error: {str(e)}"}
            self._update_langfuse_observation(output=error_response, level="ERROR")
            return error_response

    @observe()
    def process_request(self, messages: list[dict]) -> tuple[list[dict], list]:
        """
        Process user request using Claude API

        Args:
            messages: List of conversation messages

        Returns:
            Tuple of (updated_messages, assistant_message_content)
        """

        # Update Langfuse context if available
        self._update_langfuse_observation(
            name="Claude Request Processing",
            input={"messages": messages, "num_messages": len(messages)},
            metadata={"model": self.model_name},
        )

        # Make initial API request
        logging.debug(f"Making API request with {len(messages)} messages")
        logging.debug(f"Last 2 messages: {messages[-2:] if len(messages) >= 2 else messages}")
        response = self.make_api_request(messages)

        if "error" in response:
            # Return error as assistant message
            error_message = [
                {"type": "text", "text": f"❌ Error communicating with Claude: {response['error']}"}
            ]

            self._update_langfuse_observation(output=error_message, level="ERROR")
            return messages, error_message

        # Process the response
        assistant_message = response.get("content", [])

        self._update_langfuse_observation(output=assistant_message)

        return messages, assistant_message
