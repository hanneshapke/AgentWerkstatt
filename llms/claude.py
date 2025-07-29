import os
from typing import Any

import httpx
from absl import logging

from .base import BaseLLM


class ClaudeLLM(BaseLLM):
    """Claude LLM implementation with clean API handling"""

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
        return self._format_system_prompt()

    def make_api_request(self, messages: list[dict] = None) -> dict:
        """Make a request to the Claude API"""
        if not messages:
            return {"error": "No messages provided"}

        # Validate and prepare request
        try:
            sanitized_messages = self._prepare_messages(messages)
            payload = self._build_payload(sanitized_messages)

            # Execute request with observability
            return self._execute_request_with_observability(payload, sanitized_messages)

        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logging.error(f"Unexpected error in API request: {e}")
            return {"error": f"Request preparation failed: {str(e)}"}

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list]:
        """Process user request using Claude API"""
        if not messages:
            error_message = [{"type": "text", "text": "❌ No messages provided to process"}]
            return [], error_message

        logging.debug(f"Processing request with {len(messages)} messages")
        response = self.make_api_request(messages)

        if "error" in response:
            error_message = [
                {"type": "text", "text": f"❌ Error communicating with Claude: {response['error']}"}
            ]
            return messages, error_message

        assistant_message = response.get("content", [])
        if not assistant_message:
            error_message = [{"type": "text", "text": "❌ Received empty response from Claude"}]
            return messages, error_message

        return messages, assistant_message

    def _prepare_messages(self, messages: list[dict]) -> list[dict]:
        """Validate and sanitize messages for API"""
        if not self._is_valid_message_list(messages):
            raise ValueError("Invalid conversation format")

        return self._sanitize_messages(messages)

    def _is_valid_message_list(self, messages: list[dict]) -> bool:
        """Validate message list structure"""
        if not isinstance(messages, list) or not messages:
            return False

        for i, message in enumerate(messages):
            if not self._is_valid_message(message, i):
                return False

        return True

    def _is_valid_message(self, message: dict, index: int) -> bool:
        """Validate individual message structure"""
        if not isinstance(message, dict):
            logging.error(f"Message {index} is not a dict")
            return False

        # Check required fields
        for field in ["role", "content"]:
            if field not in message:
                logging.error(f"Message {index} missing '{field}' field")
                return False

        # Validate role
        if message["role"] not in ["user", "assistant", "system"]:
            logging.error(f"Message {index} has invalid role: {message['role']}")
            return False

        # Validate content
        return self._is_valid_content(message["content"], index)

    def _is_valid_content(self, content, message_index: int) -> bool:
        """Validate message content structure"""
        if isinstance(content, str):
            return bool(content.strip())
        elif isinstance(content, list):
            if not content:
                return False
            return all(
                self._is_valid_content_block(block, message_index, i)
                for i, block in enumerate(content)
            )
        else:
            logging.error(f"Message {message_index} content has invalid type: {type(content)}")
            return False

    def _is_valid_content_block(self, block: dict, message_index: int, block_index: int) -> bool:
        """Validate content block structure"""
        if not isinstance(block, dict) or "type" not in block:
            logging.error(f"Message {message_index}, block {block_index} invalid")
            return False

        block_type = block.get("type")
        required_fields = {
            "text": ["text"],
            "tool_use": ["name", "id"],
            "tool_result": ["tool_use_id", "content"],
        }

        if block_type in required_fields:
            return all(field in block for field in required_fields[block_type])

        return True  # Unknown block types are allowed

    def _sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """Sanitize messages for API safety"""
        sanitized = []
        for message in messages:
            clean_message = {"role": message["role"], "content": message["content"]}

            # Filter invalid content blocks if list
            if isinstance(clean_message["content"], list):
                clean_message["content"] = [
                    block
                    for block in clean_message["content"]
                    if isinstance(block, dict) and "type" in block
                ]

            sanitized.append(clean_message)

        return sanitized

    def _build_payload(self, messages: list[dict]) -> dict:
        """Build API request payload"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 2000,
            "system": self.system_prompt,
        }

        tool_schemas = self._get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas

        # Validate payload
        if not self._is_valid_payload(payload):
            raise ValueError("Invalid API payload")

        return payload

    def _is_valid_payload(self, payload: dict) -> bool:
        """Validate API payload structure"""
        required_fields = ["model", "messages", "max_tokens"]

        # Check required fields exist and have valid types
        if not all(field in payload for field in required_fields):
            return False

        if not isinstance(payload["model"], str) or not payload["model"]:
            return False

        if not isinstance(payload["max_tokens"], int) or payload["max_tokens"] <= 0:
            return False

        if not isinstance(payload["messages"], list) or not payload["messages"]:
            return False

        return True

    def _execute_request_with_observability(self, payload: dict, messages: list[dict]) -> dict:
        """Execute HTTP request with observability tracking"""
        # Start observability
        llm_span = self._start_llm_observation(messages)

        try:
            # Make HTTP request
            response_data = self._make_http_request(payload)

            # Update observability with success
            self._update_llm_observation_success(llm_span, response_data)

            return response_data

        except Exception as e:
            error_response = {"error": str(e)}
            self._update_llm_observation_error(llm_span, error_response)
            return error_response

    def _start_llm_observation(self, messages: list[dict]) -> Any | None:
        """Start LLM observability tracking"""
        if not self.observability_service:
            return None

        try:
            return self.observability_service.observe_llm_call(
                model_name=self.model_name,
                messages=messages,
                metadata={
                    "max_tokens": 2000,
                    "num_tools": len(self.tools) if self.tools else 0,
                    "system_prompt_length": len(self.system_prompt),
                },
            )
        except Exception as e:
            logging.error(f"Failed to start LLM observation: {e}")
            return None

    def _make_http_request(self, payload: dict) -> dict:
        """Make HTTP request to Claude API"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response_data = response.json()

                if response.status_code != 200:
                    error_info = self._extract_error_info(response_data, response.status_code)
                    raise Exception(
                        f"Claude API error ({error_info['type']}): {error_info['message']}"
                    )

                return response_data

        except httpx.TimeoutException as e:
            raise Exception("API request timed out") from e
        except httpx.ConnectError as e:
            raise Exception("Failed to connect to Claude API") from e
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error during API request: {str(e)}") from e
        except Exception as e:
            if "Claude API error" in str(e):
                raise  # Re-raise API errors as-is
            raise Exception(f"Request failed: {str(e)}") from e

    def _extract_error_info(self, response_data: dict, status_code: int) -> dict:
        """Extract error information from API response"""
        error_details = response_data.get("error", {})

        if isinstance(error_details, dict):
            return {
                "message": error_details.get("message", str(response_data)),
                "type": error_details.get("type", "unknown_error"),
            }
        else:
            return {"message": str(error_details), "type": "unknown_error"}

    def _update_llm_observation_success(self, llm_span, response_data: dict) -> None:
        """Update observability with successful response"""
        if not llm_span or not self.observability_service:
            return

        try:
            content = response_data.get("content", [])
            usage = response_data.get("usage", {})

            if usage:
                self.observability_service.update_llm_observation(
                    llm_generation=llm_span,
                    output=content,
                    usage={
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                    },
                )
            else:
                self.observability_service.update_llm_observation(
                    llm_generation=llm_span, output=content
                )
        except Exception as e:
            logging.error(f"Failed to update LLM observation: {e}")

    def _update_llm_observation_error(self, llm_span, error_response: dict) -> None:
        """Update observability with error response"""
        if not llm_span or not self.observability_service:
            return

        try:
            self.observability_service.update_llm_observation(
                llm_generation=llm_span, output=error_response
            )
        except Exception as e:
            logging.error(f"Failed to update LLM observation with error: {e}")
