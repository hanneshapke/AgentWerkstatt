#!/usr/bin/env python3
"""
Tavily Search Tool for AgentWerkstatt
Provides comprehensive web search using Tavily API
"""

import os
from typing import Any

import httpx
from absl import logging

from .base import BaseTool


class TavilySearchTool(BaseTool):
    """Tool to perform web searches using Tavily API"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://api.tavily.com/search"
        self.timeout = 15.0
        self.api_key = os.getenv("TAVILY_API_KEY")

    def _get_name(self) -> str:
        """Return the tool name"""
        return "Web search"

    def _get_description(self) -> str:
        """Return the tool description"""
        return "Search the web for comprehensive, real-time information using Google"

    def get_schema(self) -> dict[str, Any]:
        """Return the tool schema for Claude"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to look up"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5, max: 20)",
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "search_depth": {
                        "type": "string",
                        "description": "Search depth level",
                        "enum": ["basic", "advanced"],
                        "default": "basic",
                    },
                    "include_answer": {
                        "type": "boolean",
                        "description": "Whether to include a summarized answer",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        }

    def execute(self, **kwargs) -> dict[str, Any]:
        """
        Perform a web search using Tavily API

        Args:
            **kwargs: Tool parameters including:
                - query: The search query string
                - max_results: Maximum number of results (default: 5)
                - search_depth: "basic" or "advanced" (default: "basic")
                - include_answer: Whether to include AI-generated answer (default: True)

        Returns:
            Dictionary containing search results and metadata
        """

        query = kwargs.get("query")
        max_results = kwargs.get("max_results", 5)
        search_depth = kwargs.get("search_depth", "basic")
        include_answer = kwargs.get("include_answer", True)

        logging.debug(
            f"Executing Tavily search tool with query: {query} and max_results: {max_results}"
        )
        if not query:
            return {"success": False, "error": "Search query is required", "results": []}

        if not self.api_key:
            return {
                "success": False,
                "error": "Tavily API key not found. Set TAVILY_API_KEY environment variable.",
                "results": [],
                "setup_info": {
                    "sign_up": "https://app.tavily.com/",
                    "free_tier": "1,000 searches/month",
                    "pricing": "$5/month for 10K searches",
                },
            }

        # Validate max_results
        max_results = min(max(max_results, 1), 20)

        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "include_answer": include_answer,
                "include_raw_content": False,
                "max_results": max_results,
                "include_domains": [],
                "exclude_domains": [],
            }

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload)
                response.raise_for_status()
                data = response.json()

            # Process results
            results = []

            # Add AI-generated answer if available
            if data.get("answer") and include_answer:
                results.append(
                    {
                        "title": "AI Summary",
                        "snippet": data["answer"],
                        "url": "",
                        "type": "ai_answer",
                        "score": 1.0,
                    }
                )

            logging.info(f"Tavily search results: {data}")
            # Add search results
            for result in data.get("results", []):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "snippet": result.get("content", ""),
                        "url": result.get("url", ""),
                        "type": "search_result",
                        "score": result.get("score", 0.0),
                        "published_date": result.get("published_date", ""),
                    }
                )

            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_depth": search_depth,
                "response_time": data.get("response_time", ""),
                "api_provider": "Tavily",
            }

        except httpx.TimeoutException:
            return {"success": False, "error": "Search request timed out", "results": []}
        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 401:
                return {"success": False, "error": "Invalid Tavily API key", "results": []}
            elif e.response and e.response.status_code == 429:
                return {"success": False, "error": "Tavily API rate limit exceeded", "results": []}
            else:
                return {
                    "success": False,
                    "error": f"HTTP error during search: {str(e)}",
                    "results": [],
                }
        except Exception as e:
            return {"success": False, "error": f"Error performing search: {str(e)}", "results": []}
