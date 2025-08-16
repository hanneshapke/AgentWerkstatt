from .api_client import ApiClient
from .base import BaseLLM


class OllamaLLM(BaseLLM):
    """Local LLM client to connect to Ollama

    Ollama is a lightweight, open-source, and easy-to-use LLM server that allows you to run and interact with LLMs locally.
    It supports a wide range of models, including Llama, Mistral, and more.

    Ollama is a great option for local development and testing, as it doesn't require any API keys or credentials.
    Default endpoint is http://localhost:11434/api/chat
    """

    def __init__(
        self,
        persona: str,
        model_name: str,
        tools: dict,
        observability_service=None,
        base_url: str = "http://localhost:11434",
    ):
        super().__init__(model_name, tools, persona, observability_service)
        self.base_url = base_url.rstrip("/")
        self.api_client = ApiClient(
            base_url=f"{self.base_url}/api/chat",
            headers={
                "Content-Type": "application/json",
            },
        )

    def set_persona(self, persona: str):
        """Set the persona for the LLM"""
        self.persona = persona

    def make_api_request(self, messages: list[dict]) -> dict:
        """Make a request to the Ollama API"""
        if not messages:
            return {"error": "No messages provided."}

        payload = self._build_payload(messages)
        if self.observability_service:
            llm_span = self.observability_service.observe_llm_call(
                model_name=self.model_name, messages=messages
            )

        response_data = self.api_client.post(payload)

        if self.observability_service:
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

        # Handle Ollama response format
        message = response.get("message", {})
        return message.get("content", "")

    def get_info(self) -> dict:
        """
        Returns information about the model.
        """
        return {"model": self.model_name}

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Processes a list of messages, sends them to the Ollama API, and returns the conversation and assistant's response.
        """
        if not messages:
            return [], [{"type": "text", "text": "No messages to process."}]

        response = self.make_api_request(messages)

        if "error" in response:
            error_content = [{"type": "text", "text": f"Error: {response['error']}"}]
            return messages, error_content

        # Handle Ollama response format
        message = response.get("message", {})
        content = message.get("content", "")
        if content:
            assistant_content = [{"type": "text", "text": content}]
        else:
            assistant_content = [{"type": "text", "text": "No response from model."}]

        return messages, assistant_content

    def _build_payload(self, messages: list[dict]) -> dict:
        """Constructs the payload for the Ollama API request."""
        # Ollama uses a different format - system message is separate
        formatted_messages = messages.copy()

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": False,
        }

        # Add system prompt if provided
        if self.persona:
            payload["system"] = self.persona

        # Note: Tool support in Ollama is model-dependent and experimental
        tool_schemas = self._get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas

        return payload
