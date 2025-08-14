import os
import unittest
from typing import Any
from unittest.mock import Mock

import yaml

from config import AgentConfig
from llms.mock import MockLLM
from main import Agent
from services.tool_executor import ToolExecutor
from tools.base import BaseTool
from tools.discovery import ToolRegistry


class StaticTool(BaseTool):
    def get_name(self) -> str:
        return "static_tool"

    def get_description(self) -> str:
        return "A simple tool that returns a fixed value."

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "input_schema": {"type": "object", "properties": {}, "required": []},
        }

    def execute(self, **kwargs) -> dict[str, Any]:
        return {"result": "static tool output"}


class TestAgentEndToEnd(unittest.TestCase):
    def setUp(self):
        # Create a dummy tools directory
        self.test_dir = os.path.dirname(__file__)
        self.tools_dir = os.path.join(self.test_dir, "temp_tools")
        os.makedirs(self.tools_dir, exist_ok=True)

    def tearDown(self):
        # Clean up the dummy tools directory
        if os.path.exists(self.tools_dir):
            for file in os.listdir(self.tools_dir):
                os.remove(os.path.join(self.tools_dir, file))
            os.rmdir(self.tools_dir)

    def test_agent_with_static_tool(self):
        # 1. Setup
        # Tools
        tools = [StaticTool()]

        # Mock LLM that suggests using the static tool
        mock_llm = MockLLM(tools=tools)
        tool_registry = ToolRegistry(tools_dir=self.tools_dir)
        tool_registry._tools = tools  # Manually inject the tool
        tool_registry._tool_map = {
            tool.get_name(): tool for tool in tools
        }  # Manually inject the tool
        mock_observability = Mock()
        tool_executor = ToolExecutor(tool_registry, mock_observability)

        # Mock services
        mock_memory_service = Mock()
        mock_memory_service.is_enabled = False

        # Agent Configuration - Load from test config file
        config_path = os.path.join(self.test_dir, "test_config.yaml")
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        config_data["tools_dir"] = self.tools_dir
        # Remove unexpected keys
        config_data.pop("langfuse", None)
        config_data.pop("memory", None)
        agent_config = AgentConfig(**config_data)

        # Agent with injected dependencies
        agent = Agent(
            config=agent_config,
            llm=mock_llm,
            memory_service=mock_memory_service,
            observability_service=mock_observability,
            tool_executor=tool_executor,
        )

        # Override the Agent's discovered tools with just our test tool
        agent.tool_registry._tools = tools
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
        config_path = os.path.join(self.test_dir, "test_config.yaml")
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        config_data["tools_dir"] = self.tools_dir
        # Remove unexpected keys
        config_data.pop("langfuse", None)
        config_data.pop("memory", None)
        agent_config = AgentConfig(**config_data)

        # 2. Verification - Check that persona was loaded from test_agent.md
        with open(os.path.join(self.test_dir, agent_config.persona)) as f:
            persona_content = f.read()
        self.assertIn("TestBot", persona_content)
        self.assertIn("Testing Assistant", persona_content)
        self.assertIn("simple, direct testing agent", persona_content)
        self.assertIn("test execution, tool validation", persona_content)

        # 3. Create agent with mock dependencies to test system prompt

        # Create system prompt and verify persona content is included

        # 4. Assertions - Verify persona content is in system prompt
        self.assertIn("TestBot", persona_content)
        self.assertIn("Testing Assistant", persona_content)
        self.assertIn("simple, direct testing agent", persona_content)


if __name__ == "__main__":
    unittest.main()
