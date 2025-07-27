from typing import Any


class BaseLLM:
    """Abstract base class for all LLMs"""

    def __init__(self, model_name: str, tools: dict[str, Any]):
        self.model_name = model_name
        self.api_key = ""
        self.base_url = ""
        self.conversation_history = []
        self.base_system_prompt = ""
        self.tools = tools
        self.timeout = 30.0

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def make_api_request(self, messages: list[dict]) -> str:
        """Make an API request to the LLM"""
        raise NotImplementedError("Subclasses must implement this method")

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list]:
        """Process user request using LLM

        Args:
            messages: List of conversation messages

        Returns:
            Tuple of (updated_messages, assistant_message_content)
        """
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return self.base_system_prompt
