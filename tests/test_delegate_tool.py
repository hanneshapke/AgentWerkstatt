import unittest
from unittest.mock import MagicMock

from agentwerkstatt.tools.delegate import DelegateTool


class TestDelegateTool(unittest.TestCase):
    def setUp(self):
        self.tool = DelegateTool()
        self.mock_agent = MagicMock()
        self.tool.agent = self.mock_agent

    def test_execute_success(self):
        self.mock_agent.active_persona_name = "planner"
        self.mock_agent.process_request.return_value = "Task completed"

        result = self.tool.execute("coder", "Write a function")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["persona"], "coder")
        self.assertEqual(result["output"], "Task completed")
        self.mock_agent.switch_persona.assert_any_call("coder")
        self.mock_agent.switch_persona.assert_any_call("planner")
        self.mock_agent.process_request.assert_called_once_with(
            "Write a function", session_id=self.mock_agent.session_id
        )

    def test_execute_invalid_persona(self):
        self.mock_agent.switch_persona.side_effect = ValueError("Invalid persona")

        with self.assertRaises(ValueError):
            self.tool.execute("invalid", "some task")

    def test_execute_no_agent(self):
        self.tool.agent = None
        result = self.tool.execute("coder", "some task")
        self.assertEqual(result["status"], "error")
        self.assertIn("Agent instance not available", result["error"])


if __name__ == "__main__":
    unittest.main()
