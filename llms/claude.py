import os

import httpx
from dotenv import load_dotenv

from .base import BaseLLM

load_dotenv()


class ClaudeLLM(BaseLLM):
    """Claude LLM"""

    def __init__(self, model_name: str, tools: dict):
        super().__init__(model_name, tools)

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_system_prompt = """You are a helpful assistant with answering questions. You have access to two main tools:

1. **Web Search Tool (websearch_tool)**: Can search the web for information using Google

When users ask for information that requires current knowledge or web-based research, use the websearch_tool to find relevant information.

When the users asks about common questions, use the LLM to answer the question.

Always be conversational and helpful."""

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

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
            tool_schemas = [tool.get_schema() for tool in self.tools.values()]
            payload["tools"] = tool_schemas

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def process_request(self, messages: list[dict]) -> str:
        """
        Process user request using Claude API

        Args:
            user_input: User's request as a string

        Returns:
            Response string from Claude
        """
        # Make initial API request
        response = self.make_api_request(messages)

        if "error" in response:
            return f"❌ Error communicating with Claude: {response['error']}"

        # Process the response
        assistant_message = response.get("content", [])
        return messages, assistant_message
