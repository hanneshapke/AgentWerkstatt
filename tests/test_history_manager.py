import unittest

from agentwerkstatt.services.history_manager import HistoryManager


class TestHistoryManager(unittest.TestCase):
    def setUp(self):
        self.history_manager = HistoryManager()

    def test_initialization(self):
        """Test HistoryManager initialization"""
        self.assertEqual(len(self.history_manager.conversation_history), 0)
        self.assertEqual(self.history_manager.conversation_length, 0)

    def test_add_message(self):
        """Test adding a message to history"""
        self.history_manager.add_message("user", "Hello")

        self.assertEqual(len(self.history_manager.conversation_history), 1)
        self.assertEqual(self.history_manager.conversation_history[0].role, "user")
        self.assertEqual(self.history_manager.conversation_history[0].content, "Hello")

    def test_add_multiple_messages(self):
        """Test adding multiple messages"""
        self.history_manager.add_message("user", "Hello")
        self.history_manager.add_message("assistant", "Hi there!")
        self.history_manager.add_message("user", "How are you?")

        self.assertEqual(len(self.history_manager.conversation_history), 3)
        self.assertEqual(self.history_manager.conversation_length, 3)

    def test_get_history(self):
        """Test getting history as dictionaries"""
        self.history_manager.add_message("user", "Hello")
        self.history_manager.add_message("assistant", "Hi there!")

        history = self.history_manager.get_history()

        expected = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        self.assertEqual(history, expected)

    def test_get_history_empty(self):
        """Test getting history when empty"""
        history = self.history_manager.get_history()
        self.assertEqual(history, [])

    def test_clear_history(self):
        """Test clearing history"""
        # Add some messages first
        self.history_manager.add_message("user", "Hello")
        self.history_manager.add_message("assistant", "Hi there!")
        self.assertEqual(len(self.history_manager.conversation_history), 2)

        # Clear history
        self.history_manager.clear_history()

        # Verify it's empty
        self.assertEqual(len(self.history_manager.conversation_history), 0)
        self.assertEqual(self.history_manager.conversation_length, 0)
        self.assertEqual(self.history_manager.get_history(), [])

    def test_conversation_length_property(self):
        """Test conversation_length property"""
        # Initially empty
        self.assertEqual(self.history_manager.conversation_length, 0)

        # Add messages and check length
        self.history_manager.add_message("user", "Message 1")
        self.assertEqual(self.history_manager.conversation_length, 1)

        self.history_manager.add_message("assistant", "Response 1")
        self.assertEqual(self.history_manager.conversation_length, 2)

        self.history_manager.add_message("user", "Message 2")
        self.assertEqual(self.history_manager.conversation_length, 3)

    def test_message_content_preservation(self):
        """Test that message content is preserved correctly"""
        test_content = "This is a test message with special characters: !@#$%^&*()"
        self.history_manager.add_message("user", test_content)

        history = self.history_manager.get_history()
        self.assertEqual(history[0]["content"], test_content)

    def test_role_preservation(self):
        """Test that roles are preserved correctly"""
        test_roles = ["user", "assistant", "system", "custom_role"]

        for role in test_roles:
            self.history_manager.add_message(role, f"Message from {role}")

        history = self.history_manager.get_history()
        for i, role in enumerate(test_roles):
            self.assertEqual(history[i]["role"], role)


if __name__ == "__main__":
    unittest.main()
