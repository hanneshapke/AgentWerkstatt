import unittest
from typing import Any
from unittest.mock import Mock

from agentwerkstatt.agent import Agent
from agentwerkstatt.config import AgentConfig
from agentwerkstatt.interfaces import Message
from agentwerkstatt.llms.mock import MockLLM
from agentwerkstatt.services.conversation_handler import ConversationHandler
from agentwerkstatt.services.tool_executor import ToolExecutor
from agentwerkstatt.tools.base import BaseTool
from agentwerkstatt.tools.discovery import ToolRegistry


class StaticTool(BaseTool):
    def _get_name(self) -> str:
        return "static_tool"

    def _get_description(self) -> str:
        return "A simple tool that returns a fixed value."

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.get_name(),
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    def execute(self, **kwargs) -> dict[str, Any]:
        return {"result": "static tool output"}


class TestAgentEndToEnd(unittest.TestCase):
    def test_agent_with_static_tool(self):
        # 1. Setup
        # Tools
        tools = [StaticTool()]

        # Mock LLM that suggests using the static tool
        mock_llm = MockLLM(tools=tools)
        tool_registry = ToolRegistry(tools=tools)
        mock_observability = Mock()
        tool_executor = ToolExecutor(tool_registry, mock_observability)

        # Mock services
        mock_memory_service = Mock()
        mock_memory_service.is_enabled = False

        # Agent Configuration
        agent_config = AgentConfig(
            model="mock-model",
            tools_dir="",  # Empty to prevent tool discovery
            verbose=False,
            persona="Test agent"
        )

        # Agent with injected dependencies
        agent = Agent(
            config=agent_config,
            llm=mock_llm,
            memory_service=mock_memory_service,
            observability_service=mock_observability,
            tool_executor=tool_executor
        )

        # Override the Agent's discovered tools with just our test tool
        agent.tools = tools
        mock_llm.tools = tools

        # 2. Execution
        prompt = "Use the static tool"
        response = agent.process_request(prompt)

        # 3. Assertion
        self.assertIn("static tool output", response)


if __name__ == "__main__":
    unittest.main()
