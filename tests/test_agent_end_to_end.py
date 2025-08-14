import os
import unittest
from typing import Any
from unittest.mock import Mock

from agentwerkstatt.agent import Agent
from agentwerkstatt.config import AgentConfig
from agentwerkstatt.llms.mock import MockLLM
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
            "input_schema": {"type": "object", "properties": {}, "required": []},
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

        # Agent Configuration - Load from test config file
        test_dir = os.path.dirname(__file__)
        config_path = os.path.join(test_dir, "test_config.yaml")
        agent_config = AgentConfig.from_yaml(config_path)

        # Agent with injected dependencies
        agent = Agent(
            config=agent_config,
            llm=mock_llm,
            memory_service=mock_memory_service,
            observability_service=mock_observability,
            tool_executor=tool_executor,
        )

        # Override the Agent's discovered tools with just our test tool
        agent.tools = tools
        mock_llm.tools = tools

        # 2. Execution
        prompt = "Use the static tool"
        response = agent.process_request(prompt)

        # 3. Assertion
        self.assertIn("static tool output", response)

    def test_agent_persona_in_system_prompt(self):
        """Test that the persona from test_agent.md is properly loaded and used"""
        # 1. Setup
        # Load configuration from test files
        test_dir = os.path.dirname(__file__)
        config_path = os.path.join(test_dir, "test_config.yaml")
        agent_config = AgentConfig.from_yaml(config_path)

        # 2. Verification - Check that persona was loaded from test_agent.md
        self.assertIn("TestBot", agent_config.persona)
        self.assertIn("Testing Assistant", agent_config.persona)
        self.assertIn("simple, direct testing agent", agent_config.persona)
        self.assertIn("test execution, tool validation", agent_config.persona)

        # 3. Create agent with mock dependencies to test system prompt
        tools = [StaticTool()]
        mock_llm = MockLLM(persona=agent_config.persona, tools=tools)

        # Create system prompt and verify persona content is included
        system_prompt = mock_llm._format_system_prompt()

        # 4. Assertions - Verify persona content is in system prompt
        self.assertIn("TestBot", system_prompt)
        self.assertIn("Testing Assistant", system_prompt)
        self.assertIn("simple, direct testing agent", system_prompt)


if __name__ == "__main__":
    unittest.main()
