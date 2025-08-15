from ..interfaces import Message


class HistoryManager:
    """Manages the conversation history."""

    def __init__(self):
        self.conversation_history: list[Message] = []

    def add_message(self, role: str, content: str):
        """Adds a message to the history."""
        self.conversation_history.append(Message(role=role, content=content))

    def get_history(self) -> list[dict]:
        """Returns the conversation history as a list of dictionaries."""
        return [{"role": msg.role, "content": msg.content} for msg in self.conversation_history]

    def clear_history(self):
        """Clears the conversation history."""
        self.conversation_history = []

    @property
    def conversation_length(self) -> int:
        """Returns the number of messages in the conversation history."""
        return len(self.conversation_history)
