class ResponseMessageFormatter:
    """Formats the final response to the user."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def prepend_persona_to_response(self, response_text: str) -> str:
        """Prepend the active persona name to the response text."""
        return f"[{self.agent_name}] {response_text}"

    def extract_text_from_response(self, content: list[dict]) -> str:
        """Extract text content from Claude response"""
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return "".join(text_parts)
