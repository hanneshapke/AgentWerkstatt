import os

import httpx
from absl import logging
from dotenv import load_dotenv

from .base import BaseLLM

load_dotenv()


class ClaudeLLM(BaseLLM):
    """Claude LLM"""

    def __init__(self, agent_objective: str, model_name: str, tools: dict):
        super().__init__(model_name, tools)

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.agent_objective = agent_objective
        self.base_system_prompt = """
{agent_objective}

You have {num_tools} tools at your disposal:

{tool_descriptions}
""".strip()

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    @property
    def system_prompt(self) -> str:
        """Get the system prompt"""

        tool_descriptions = ""
        for tool in self.tools:
            tool_descriptions += (
                f"{tool.get_name()} ({tool.get_function_name()}): {tool.description}\n"
            )
        _system_prompt = self.base_system_prompt.format(
            agent_objective=self.agent_objective,
            num_tools=len(self.tools),
            tool_descriptions=tool_descriptions,
        )
        logging.debug(f"System prompt: {_system_prompt}")
        return _system_prompt

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

        if self.tools:
            tool_schemas = [tool.get_schema() for tool in self.tools]
            payload["tools"] = tool_schemas

        logging.debug(f"Making API request with payload: {payload}")
        logging.debug(f"Headers: {headers}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                logging.debug(f"Response: {response.json()}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

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
