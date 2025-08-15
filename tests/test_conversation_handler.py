import unittest
from unittest.mock import MagicMock, patch

from agentwerkstatt.services.conversation_handler import ConversationHandler


class TestConversationHandler(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.mock_agent = MagicMock()
        self.mock_agent.active_persona_name = "test_persona"
        self.mock_memory_service = MagicMock()
        self.mock_observability_service = MagicMock()
        self.mock_tool_interaction_handler = MagicMock()
        self.mock_user_id_provider = MagicMock(return_value="test_user")

        with patch(
            "agentwerkstatt.services.conversation_handler.HistoryManager"
        ) as mock_history_class:
            with patch(
                "agentwerkstatt.services.conversation_handler.ResponseMessageFormatter"
            ) as mock_formatter_class:
                self.mock_history_manager = MagicMock()
                self.mock_response_formatter = MagicMock()
                mock_history_class.return_value = self.mock_history_manager
                mock_formatter_class.return_value = self.mock_response_formatter

                self.handler = ConversationHandler(
                    llm=self.mock_llm,
                    agent=self.mock_agent,
                    memory_service=self.mock_memory_service,
                    observability_service=self.mock_observability_service,
                    tool_interaction_handler=self.mock_tool_interaction_handler,
                    user_id_provider=self.mock_user_id_provider,
                )

    def test_enhance_input_with_memory_success(self):
        """Test successful memory enhancement"""
        self.mock_memory_service.retrieve_memories.return_value = "memory context"

        result = self.handler.enhance_input_with_memory("test input")

        self.assertEqual(result, "memory context\n\nUser query: test input")
        self.mock_memory_service.retrieve_memories.assert_called_once_with(
            "test input", "test_user"
        )

    def test_enhance_input_with_memory_no_context(self):
        """Test memory enhancement with no context returned"""
        self.mock_memory_service.retrieve_memories.return_value = ""

        result = self.handler.enhance_input_with_memory("test input")

        self.assertEqual(result, "test input")

    def test_enhance_input_with_memory_exception(self):
        """Test memory enhancement with exception"""
        self.mock_memory_service.retrieve_memories.side_effect = Exception("Memory error")

        with patch("agentwerkstatt.services.conversation_handler.logging.warning") as mock_warning:
            result = self.handler.enhance_input_with_memory("test input")
            mock_warning.assert_called_once()

        self.assertEqual(result, "test input")

    def test_process_message_without_tools(self):
        """Test message processing without tool calls"""
        self.mock_history_manager.get_history.return_value = []
        self.mock_llm.process_request.return_value = (None, [{"content": "response"}])
        self.mock_tool_interaction_handler.handle_tool_calls.return_value = ([], [])
        self.mock_response_formatter.extract_text_from_response.return_value = "final response"

        result = self.handler.process_message("user input", "enhanced input")

        self.assertEqual(result, "final response")
        self.mock_history_manager.add_message.assert_any_call("user", "user input")
        self.mock_history_manager.add_message.assert_any_call("assistant", "final response")

    def test_process_message_with_tools(self):
        """Test message processing with tool calls"""
        self.mock_history_manager.get_history.return_value = []
        self.mock_llm.process_request.return_value = (None, [{"content": "response"}])
        tool_results = [{"result": "tool output"}]
        self.mock_tool_interaction_handler.handle_tool_calls.return_value = (tool_results, [])

        # Mock _handle_tool_response
        with patch.object(self.handler, "_handle_tool_response", return_value="tool response"):
            result = self.handler.process_message("user input", "enhanced input")

        self.assertEqual(result, "tool response")

    def test_process_message_exception(self):
        """Test message processing with exception"""
        self.mock_history_manager.get_history.side_effect = Exception("Processing error")

        with patch.object(
            self.handler, "_create_error_response", return_value="error response"
        ) as mock_error:
            result = self.handler.process_message("user input", "enhanced input")
            mock_error.assert_called_once_with("user input", "Processing error")

        self.assertEqual(result, "error response")

    def test_handle_tool_response(self):
        """Test tool response handling"""
        messages = [{"role": "user", "content": "test"}]
        assistant_message = [{"content": "assistant response"}]
        tool_results = [{"result": "tool output"}]

        # Mock all the dependencies for _handle_tool_response
        self.mock_tool_interaction_handler.format_tool_results.return_value = "formatted tools"
        self.mock_llm.process_request.return_value = (
            None,
            {"content": [{"text": "final response"}]},
        )
        self.mock_response_formatter.extract_text_from_response.return_value = "extracted text"
        self.mock_response_formatter.prepend_persona_to_response.return_value = "persona response"

        result = self.handler._handle_tool_response(
            messages, assistant_message, tool_results, "user input"
        )

        self.assertEqual(result, "persona response")
        self.mock_history_manager.add_message.assert_any_call("user", "user input")
        self.mock_history_manager.add_message.assert_any_call("assistant", "persona response")

    def test_finalize_conversation_success(self):
        """Test successful conversation finalization"""
        self.handler._finalize_conversation("user input", "response")

        self.mock_memory_service.store_conversation.assert_called_once_with(
            "user input", "response", "test_user"
        )
        self.mock_observability_service.update_observation.assert_called_once_with("response")
        self.mock_observability_service.flush_traces.assert_called_once()

    def test_finalize_conversation_memory_error(self):
        """Test conversation finalization with memory storage error"""
        self.mock_memory_service.store_conversation.side_effect = Exception("Memory store error")

        with patch("agentwerkstatt.services.conversation_handler.logging.warning") as mock_warning:
            self.handler._finalize_conversation("user input", "response")
            mock_warning.assert_called_once()

        # Should still update observability even if memory fails
        self.mock_observability_service.update_observation.assert_called_once_with("response")

    def test_create_error_response(self):
        """Test error response creation"""
        with patch.object(self.handler, "_finalize_conversation") as mock_finalize:
            result = self.handler._create_error_response("user input", "test error")
            mock_finalize.assert_called_once_with(
                "user input", "❌ Error processing request: test error"
            )

        self.assertEqual(result, "❌ Error processing request: test error")

    def test_clear_history(self):
        """Test history clearing"""
        self.handler.clear_history()
        self.mock_history_manager.clear_history.assert_called_once()

    def test_conversation_length(self):
        """Test conversation length property"""
        self.mock_history_manager.conversation_length = 5
        self.assertEqual(self.handler.conversation_length, 5)


if __name__ == "__main__":
    unittest.main()
