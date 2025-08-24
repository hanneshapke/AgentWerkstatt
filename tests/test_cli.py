# import unittest
# from unittest.mock import MagicMock, patch

# from absl import flags

# from agentwerkstatt.cli import (
#     _handle_user_command,
#     _print_welcome_message,
#     _run_interactive_loop,
#     main,
# )


# class TestCli(unittest.TestCase):
#     def setUp(self):
#         self.mock_agent = MagicMock()
#         self.flags = flags.FLAGS
#         self.flags.mark_as_parsed()

#     def test_handle_user_command_quit(self):
#         self.mock_agent.observability_service.is_enabled = True
#         self.assertTrue(_handle_user_command("quit", self.mock_agent))
#         self.mock_agent.observability_service.flush_traces.assert_called_once()

#     def test_handle_user_command_quit_with_observability_disabled(self):
#         self.mock_agent.observability_service.is_enabled = False
#         self.assertTrue(_handle_user_command("quit", self.mock_agent))
#         self.mock_agent.observability_service.flush_traces.assert_not_called()

#     def test_handle_user_command_exit(self):
#         self.assertTrue(_handle_user_command("exit", self.mock_agent))

#     def test_handle_user_command_clear(self):
#         self.assertTrue(_handle_user_command("clear", self.mock_agent))
#         self.mock_agent.conversation_handler.clear_history.assert_called_once()

#     def test_handle_user_command_status(self):
#         self.assertTrue(_handle_user_command("status", self.mock_agent))

#     def test_handle_user_command_unknown(self):
#         self.assertFalse(_handle_user_command("unknown", self.mock_agent))

#     @patch("builtins.input", side_effect=["hello", "quit"])
#     @patch("builtins.print")
#     def test_run_interactive_loop(self, mock_print, mock_input):
#         self.mock_agent.observability_service.is_enabled = False
#         _run_interactive_loop(self.mock_agent, "test_session")
#         self.mock_agent.process_request.assert_called_once_with("hello", session_id="test_session")

#     @patch("agentwerkstatt.cli.AgentConfig.from_yaml")
#     @patch("agentwerkstatt.cli.Agent")
#     @patch("agentwerkstatt.cli._run_interactive_loop")
#     def test_main(self, mock_run_interactive_loop, mock_agent_class, mock_config):
#         self.flags.config = "test_config.yaml"
#         main([])
#         mock_config.assert_called_once_with("test_config.yaml")
#         mock_agent_class.assert_called_once()
#         mock_run_interactive_loop.assert_called_once()

#     @patch("builtins.print")
#     def test_print_welcome_message_with_memory_and_observability(self, mock_print):
#         self.mock_agent.memory_service.is_enabled = True
#         self.mock_agent.observability_service.is_enabled = True
#         _print_welcome_message(self.mock_agent, "test_session_id")
#         self.assertEqual(mock_print.call_count, 7)

#     @patch("builtins.input", side_effect=KeyboardInterrupt)
#     @patch("builtins.print")
#     def test_run_interactive_loop_keyboard_interrupt(self, mock_print, mock_input):
#         self.mock_agent.observability_service.is_enabled = True
#         _run_interactive_loop(self.mock_agent, "test_session")
#         self.mock_agent.observability_service.flush_traces.assert_called_once()

#     @patch("builtins.input", side_effect=Exception("Test exception"))
#     @patch("builtins.print")
#     @patch("agentwerkstatt.cli.logging")
#     def test_run_interactive_loop_exception(self, mock_logging, mock_print, mock_input):
#         # To break the while true loop
#         self.mock_agent.process_request.side_effect = Exception("Break loop")
#         _run_interactive_loop(self.mock_agent, "test_session")
#         mock_logging.error.assert_called()

#     @patch("agentwerkstatt.cli.AgentConfig.from_yaml", side_effect=Exception("YAML error"))
#     @patch("agentwerkstatt.cli.logging")
#     def test_main_config_error(self, mock_logging, mock_config):
#         self.flags.config = "test_config.yaml"
#         result = main([])
#         self.assertEqual(result, 1)
#         mock_logging.error.assert_called_once()

#     @patch("agentwerkstatt.cli.AgentConfig.from_yaml")
#     @patch("agentwerkstatt.cli.Agent", side_effect=Exception("Agent error"))
#     @patch("agentwerkstatt.cli.logging")
#     def test_main_agent_init_error(self, mock_logging, mock_agent_class, mock_config):
#         self.flags.config = "test_config.yaml"
#         result = main([])
#         self.assertEqual(result, 1)
#         mock_logging.error.assert_called_once()


# if __name__ == "__main__":
#     unittest.main()
