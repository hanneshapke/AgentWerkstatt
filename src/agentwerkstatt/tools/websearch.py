import os
from typing import Any

import httpx
from absl import logging

from .base import BaseTool


class TavilySearchTool(BaseTool):
    """A tool for performing web searches using the Tavily API."""

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"
        self.timeout = 60.0

    def get_name(self) -> str:
        return "web_search"

    def get_description(self) -> str:
        return "Searches the web for real-time information, news, and answers using the Tavily search engine."

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to look up."},
                    "max_results": {
                        "type": "integer",
                        "description": "The maximum number of results to return (default: 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }

    def execute(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """
        Executes a web search with the given query.
        """
        if not self.api_key:
            return {"error": "Tavily API key (TAVILY_API_KEY) is not set."}
        if not query:
            return {"error": "A search query must be provided."}

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": min(max(max_results, 1), 20),  # Clamp between 1 and 20
            "search_depth": "basic",
            "include_answer": True,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error {e.response.status_code}: {e.response.text}"
            logging.error(f"Tavily API request failed: {error_message}")
            return {"error": error_message}
        except httpx.RequestError as e:
            logging.error(f"Network error during Tavily search: {e}")
            return {"error": f"Network error: {e}"}
        except Exception as e:
            logging.error(f"An unexpected error occurred during Tavily search: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {e}"}
