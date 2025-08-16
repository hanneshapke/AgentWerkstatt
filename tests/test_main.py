import unittest
from unittest.mock import MagicMock, patch

from agentwerkstatt.config import AgentConfig
from agentwerkstatt.main import Agent


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=AgentConfig)
        self.mock_config.llm = MagicMock()
        self.mock_config.llm.provider = "claude"
        self.mock_config.llm.model = "test-model"
        self.mock_config.default_persona = "test"
        self.mock_config.tools_dir = "tools"
        self.mock_config.verbose = False
        self.mock_config.langfuse = MagicMock()
        self.mock_config.langfuse.enabled = False
        self.mock_config.memory = MagicMock()
        self.mock_config.memory.enabled = False
        self.mock_config.personas = [
            MagicMock(id="test", file="test.md"),
            MagicMock(id="other", file="other.md"),
        ]

    @patch("agentwerkstatt.main.ToolRegistry")
    def test_switch_persona(self, mock_tool_registry):
        agent = Agent(self.mock_config)
        agent.llm = MagicMock()
        agent.switch_persona("other")
        self.assertEqual(agent.active_persona_name, "other")
        agent.llm.set_persona.assert_called_once_with("other.md")

    @patch("agentwerkstatt.main.ToolRegistry")
    def test_switch_persona_not_found(self, mock_tool_registry):
        agent = Agent(self.mock_config)
        with self.assertRaises(ValueError):
            agent.switch_persona("non_existent")


if __name__ == "__main__":
    unittest.main()
