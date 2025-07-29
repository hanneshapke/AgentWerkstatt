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

    def _validate_conversation_for_api(self, messages: list[dict]) -> tuple[bool, str]:
        """Validate conversation messages before sending to Claude API"""
        if not messages:
            return False, "No messages provided"

        if not isinstance(messages, list):
            return False, f"Messages must be a list, got {type(messages)}"

        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                return False, f"Message {i} is not a dict: {type(message)}"

            if "role" not in message:
                return False, f"Message {i} missing 'role' field"

            if "content" not in message:
                return False, f"Message {i} missing 'content' field"

            role = message["role"]
            if role not in ["user", "assistant", "system"]:
                return False, f"Message {i} has invalid role: {role}"

            content = message["content"]
            if isinstance(content, str):
                if not content.strip():
                    return False, f"Message {i} has empty content"
            elif isinstance(content, list):
                if not content:
                    return False, f"Message {i} has empty content list"

                for j, block in enumerate(content):
                    if not isinstance(block, dict):
                        return False, f"Message {i}, content block {j} is not a dict"

                    if "type" not in block:
                        return False, f"Message {i}, content block {j} missing 'type'"

                    block_type = block.get("type")
                    if block_type == "text" and "text" not in block:
                        return (
                            False,
                            f"Message {i}, content block {j} of type 'text' missing 'text' field",
                        )
                    elif block_type == "tool_use" and ("name" not in block or "id" not in block):
                        return (
                            False,
                            f"Message {i}, content block {j} of type 'tool_use' missing required fields",
                        )
                    elif block_type == "tool_result" and (
                        "tool_use_id" not in block or "content" not in block
                    ):
                        return (
                            False,
                            f"Message {i}, content block {j} of type 'tool_result' missing required fields",
                        )
            else:
                return False, f"Message {i} content has invalid type: {type(content)}"

        return True, ""

    def _sanitize_messages_for_api(self, messages: list[dict]) -> list[dict]:
        """Sanitize messages to ensure they're safe for Claude API"""
        sanitized = []

        for message in messages:
            # Create a clean copy
            clean_message = {"role": message["role"], "content": message["content"]}

            # Ensure content is properly formatted
            if isinstance(clean_message["content"], list):
                # Filter out any invalid content blocks
                valid_blocks = []
                for block in clean_message["content"]:
                    if isinstance(block, dict) and "type" in block:
                        valid_blocks.append(block)

                clean_message["content"] = valid_blocks

            sanitized.append(clean_message)

        return sanitized

    def make_api_request(self, messages: list[dict] = None) -> dict:
        """Make a request to the Claude API"""

        if not messages:
            return {"error": "No messages provided"}

        # Validate conversation format
        is_valid, error_message = self._validate_conversation_for_api(messages)
        if not is_valid:
            error_msg = f"Invalid conversation format: {error_message}"
            logging.error(error_msg)
            return {"error": error_msg}

        # Sanitize messages
        try:
            sanitized_messages = self._sanitize_messages_for_api(messages)
        except Exception as e:
            error_msg = f"Failed to sanitize messages: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}

        # Start observing this LLM call
        llm_span = None
        if self.observability_service:
            try:
                logging.debug(f"Starting LLM observation for {self.model_name}")
                llm_span = self.observability_service.observe_llm_call(
                    model_name=self.model_name,
                    messages=sanitized_messages,
                    metadata={
                        "max_tokens": 2000,
                        "num_tools": len(self.tools) if self.tools else 0,
                        "system_prompt_length": len(self.system_prompt),
                    },
                )
                logging.debug(f"LLM observation started successfully: {llm_span is not None}")
            except Exception as e:
                logging.error(f"Failed to start LLM observation: {e}")
                # Continue without observation rather than failing

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model_name,
            "messages": sanitized_messages,
            "max_tokens": 2000,
            "system": self.system_prompt,
        }

        tool_schemas = self._get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas

        logging.debug(f"Making API request with {len(sanitized_messages)} sanitized messages")
        logging.debug(f"Model name: {self.model_name}")
        logging.debug(f"Number of tools: {len(tool_schemas) if tool_schemas else 0}")

        logging.debug(f"API Key present: {bool(self.api_key)}")
        logging.debug(f"API Key prefix: {self.api_key[:10] if self.api_key else 'None'}...")

        # Validate payload before sending
        validation_result = self._validate_api_payload(payload, messages)
        if not validation_result["valid"]:
            error_response = {"error": f"Invalid API payload: {validation_result['error']}"}
            logging.error(f"Payload validation failed: {validation_result['error']}")
            if llm_span:
                try:
                    logging.debug("Updating LLM observation with validation error")
                    self.observability_service.update_llm_observation(
                        llm_generation=llm_span, output=error_response
                    )
                    logging.debug("LLM observation updated with validation error successfully")
                except Exception as e:
                    logging.error(f"Failed to update LLM observation with validation error: {e}")
            return error_response

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload, headers=headers)

                # Log response details before processing
                logging.debug(f"Response status: {response.status_code}")

                # Get response data safely
                try:
                    response_data = response.json()
                except Exception as e:
                    error_msg = f"Failed to parse API response as JSON: {str(e)}"
                    logging.error(error_msg)
                    return {"error": error_msg}

                logging.debug(f"Response: {response_data}")

                # Check for error before raising
                if response.status_code != 200:
                    error_details = response_data.get("error", {})
                    if isinstance(error_details, dict):
                        error_msg = error_details.get("message", str(response_data))
                        error_type = error_details.get("type", "unknown_error")
                    else:
                        error_msg = str(error_details)
                        error_type = "unknown_error"

                    logging.error(f"API Error {response.status_code} ({error_type}): {error_msg}")

                    # Update observability with error
                    if llm_span:
                        try:
                            logging.debug(f"Updating LLM observation with error: {error_msg}")
                            self.observability_service.update_llm_observation(
                                llm_generation=llm_span,
                                output={"error": error_msg, "status_code": response.status_code},
                            )
                            logging.debug("LLM observation updated with error successfully")
                        except Exception as e:
                            logging.error(f"Failed to update LLM observation with error: {e}")

                    return {"error": f"Claude API error ({error_type}): {error_msg}"}

                # Update observability with response data
                if llm_span:
                    try:
                        logging.debug("Updating LLM observation with response data")
                        if "usage" in response_data:
                            usage = response_data.get("usage", {})
                            logging.debug(f"Response includes usage data: {usage}")
                            self.observability_service.update_llm_observation(
                                llm_generation=llm_span,
                                output=response_data.get("content", []),
                                usage={
                                    "input_tokens": usage.get("input_tokens", 0),
                                    "output_tokens": usage.get("output_tokens", 0),
                                },
                            )
                        else:
                            logging.debug("Response does not include usage data")
                            self.observability_service.update_llm_observation(
                                llm_generation=llm_span, output=response_data.get("content", [])
                            )
                        logging.debug("LLM observation updated successfully")
                    except Exception as e:
                        logging.error(f"Failed to update LLM observation with success: {e}")
                        # Continue execution even if observation fails

                return response_data

        except httpx.TimeoutException as e:
            error_msg = f"API request timed out: {str(e)}"
            logging.error(error_msg)
            error_response = {"error": error_msg}
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to Claude API: {str(e)}"
            logging.error(error_msg)
            error_response = {"error": error_msg}
        except httpx.HTTPError as e:
            error_msg = f"HTTP error during API request: {str(e)}"
            logging.error(error_msg)
            error_response = {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during API request: {str(e)}"
            logging.error(error_msg)
            error_response = {"error": error_msg}

        # Update observability with error
        if llm_span:
            try:
                logging.debug("Updating LLM observation with exception error")
                self.observability_service.update_llm_observation(
                    llm_generation=llm_span, output=error_response
                )
                logging.debug("LLM observation updated with exception error successfully")
            except Exception as e:
                logging.error(f"Failed to update LLM observation with error: {e}")

        return error_response

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list]:
        """
        Process user request using Claude API

        Args:
            messages: List of conversation messages

        Returns:
            Tuple of (updated_messages, assistant_message_content)
        """

        if not messages:
            error_message = [{"type": "text", "text": "❌ No messages provided to process"}]
            return [], error_message

        # Make initial API request
        logging.debug(f"Processing request with {len(messages)} messages")
        response = self.make_api_request(messages)

        if "error" in response:
            # Return error as assistant message
            error_message = [
                {"type": "text", "text": f"❌ Error communicating with Claude: {response['error']}"}
            ]
            return messages, error_message

        # Process the response
        assistant_message = response.get("content", [])

        if not assistant_message:
            # Handle empty response
            error_message = [{"type": "text", "text": "❌ Received empty response from Claude"}]
            return messages, error_message

        return messages, assistant_message

    def _validate_api_payload(self, payload: dict, messages: list[dict]) -> dict:
        """
        Validate the API payload before sending to Claude

        Returns:
            dict: {"valid": bool, "error": str}
        """
        try:
            # Check required fields
            required_fields = ["model", "messages", "max_tokens"]
            for field in required_fields:
                if field not in payload:
                    return {"valid": False, "error": f"Missing required field: {field}"}

            # Validate model
            if not isinstance(payload["model"], str) or not payload["model"]:
                return {"valid": False, "error": "Model must be a non-empty string"}

            # Validate max_tokens
            if not isinstance(payload["max_tokens"], int) or payload["max_tokens"] <= 0:
                return {"valid": False, "error": "max_tokens must be a positive integer"}

            # Validate messages structure
            if not isinstance(payload["messages"], list):
                return {"valid": False, "error": "Messages must be a list"}

            if len(payload["messages"]) == 0:
                return {"valid": False, "error": "Messages list cannot be empty"}

            # Validate each message
            for i, message in enumerate(payload["messages"]):
                if not isinstance(message, dict):
                    return {"valid": False, "error": f"Message {i} must be a dictionary"}

                if "role" not in message:
                    return {"valid": False, "error": f"Message {i} missing 'role' field"}

                if "content" not in message:
                    return {"valid": False, "error": f"Message {i} missing 'content' field"}

                role = message["role"]
                if role not in ["user", "assistant", "system"]:
                    return {"valid": False, "error": f"Message {i} has invalid role: {role}"}

                # Validate content structure for complex messages
                content = message["content"]
                if isinstance(content, list):
                    # Validate structured content blocks
                    for j, block in enumerate(content):
                        if not isinstance(block, dict):
                            return {
                                "valid": False,
                                "error": f"Message {i} content block {j} must be a dictionary",
                            }

                        if "type" not in block:
                            return {
                                "valid": False,
                                "error": f"Message {i} content block {j} missing 'type' field",
                            }

                        block_type = block["type"]
                        if block_type == "tool_use":
                            # Validate tool_use block
                            required_tool_fields = ["id", "name", "input"]
                            for field in required_tool_fields:
                                if field not in block:
                                    return {
                                        "valid": False,
                                        "error": f"Message {i} tool_use block missing '{field}' field",
                                    }

                        elif block_type == "tool_result":
                            # Validate tool_result block
                            required_result_fields = ["tool_use_id", "content"]
                            for field in required_result_fields:
                                if field not in block:
                                    return {
                                        "valid": False,
                                        "error": f"Message {i} tool_result block missing '{field}' field",
                                    }

                        elif block_type == "text":
                            # Validate text block
                            if "text" not in block:
                                return {
                                    "valid": False,
                                    "error": f"Message {i} text block missing 'text' field",
                                }

            # Validate system prompt if present
            if "system" in payload:
                if not isinstance(payload["system"], str):
                    return {"valid": False, "error": "System prompt must be a string"}

            # Validate tools if present
            if "tools" in payload:
                if not isinstance(payload["tools"], list):
                    return {"valid": False, "error": "Tools must be a list"}

                for i, tool in enumerate(payload["tools"]):
                    if not isinstance(tool, dict):
                        return {"valid": False, "error": f"Tool {i} must be a dictionary"}

                    required_tool_fields = ["name", "description", "input_schema"]
                    for field in required_tool_fields:
                        if field not in tool:
                            return {"valid": False, "error": f"Tool {i} missing '{field}' field"}

            return {"valid": True, "error": ""}

        except Exception as e:
            return {"valid": False, "error": f"Payload validation error: {str(e)}"}
