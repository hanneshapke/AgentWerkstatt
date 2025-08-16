from .api_client import ApiClient
from .base import BaseLLM


class LMStudioLLM(BaseLLM):
    """Local LLM client to connect to LMStudio

    LMStudio provides an OpenAI-compatible API endpoint for local language models.
    Default endpoint is http://localhost:1234/v1/chat/completions
    """

    def __init__(
        self,
        persona: str,
        model_name: str,
        tools: dict,
        observability_service=None,
        base_url: str = "http://localhost:1234",
    ):
        super().__init__(model_name, tools, persona, observability_service)
        self.base_url = base_url.rstrip("/")
        self.api_client = ApiClient(
            base_url=f"{self.base_url}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
            },
        )

    def set_persona(self, persona: str):
        """Set the persona for the LLM"""
        self.persona = persona

    def make_api_request(self, messages: list[dict]) -> dict:
        """Make a request to the LMStudio API using OpenAI-compatible format"""
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

        # Handle OpenAI-compatible response format
        choices = response.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""

    def get_info(self) -> dict:
        """
        Returns information about the model.
        """
        return {"model": self.model_name}

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Processes a list of messages, sends them to the LMStudio API, and returns the conversation and assistant's response.
        """
        if not messages:
            return [], [{"type": "text", "text": "No messages to process."}]

        response = self.make_api_request(messages)

        if "error" in response:
            error_content = [{"type": "text", "text": f"Error: {response['error']}"}]
            return messages, error_content

        # Handle OpenAI-compatible response format
        choices = response.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            assistant_content = [{"type": "text", "text": content}]
        else:
            assistant_content = [{"type": "text", "text": "No response from model."}]

        return messages, assistant_content

    def _build_payload(self, messages: list[dict]) -> dict:
        """Constructs the payload for the LMStudio API request (OpenAI-compatible format)."""
        # Add system message if persona is provided
        formatted_messages = []
        if self.persona:
            formatted_messages.append({"role": "system", "content": self.persona})
        formatted_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "max_tokens": 2000,
            "temperature": 0.7,
        }

        # Note: Tool support varies by model in LMStudio
        tool_schemas = self._get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas

        return payload
