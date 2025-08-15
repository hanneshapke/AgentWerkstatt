import unittest
from unittest.mock import MagicMock, patch

from absl import flags

from agentwerkstatt.cli import _handle_user_command, _run_interactive_loop, main


class TestCli(unittest.TestCase):
    def setUp(self):
        self.mock_agent = MagicMock()
        self.flags = flags.FLAGS
        self.flags.mark_as_parsed()

    def test_handle_user_command_quit(self):
        self.assertTrue(_handle_user_command("quit", self.mock_agent))
        self.mock_agent.observability_service.flush_traces.assert_called_once()

    def test_handle_user_command_exit(self):
        self.assertTrue(_handle_user_command("exit", self.mock_agent))

    def test_handle_user_command_clear(self):
        self.assertTrue(_handle_user_command("clear", self.mock_agent))
        self.mock_agent.conversation_handler.clear_history.assert_called_once()

    def test_handle_user_command_status(self):
        self.assertTrue(_handle_user_command("status", self.mock_agent))

    def test_handle_user_command_unknown(self):
        self.assertFalse(_handle_user_command("unknown", self.mock_agent))

    @patch("builtins.input", side_effect=["hello", "quit"])
    @patch("builtins.print")
    def test_run_interactive_loop(self, mock_print, mock_input):
        _run_interactive_loop(self.mock_agent, "test_session")
        self.mock_agent.process_request.assert_called_once_with("hello", session_id="test_session")

    @patch("agentwerkstatt.cli.AgentConfig.from_yaml")
    @patch("agentwerkstatt.cli.Agent")
    @patch("agentwerkstatt.cli._run_interactive_loop")
    def test_main(self, mock_run_interactive_loop, mock_agent_class, mock_config):
        self.flags.config = "test_config.yaml"
        main([])
        mock_config.assert_called_once_with("test_config.yaml")
        mock_agent_class.assert_called_once()
        mock_run_interactive_loop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
