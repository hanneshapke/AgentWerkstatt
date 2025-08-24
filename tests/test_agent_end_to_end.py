# import unittest
# import tempfile
# import yaml
# from pathlib import Path
# from typing import Any
# from unittest.mock import Mock

# from agentwerkstatt.config import AgentConfig
# from agentwerkstatt.llms.mock import MockLLM
# from agentwerkstatt.main import Agent
# from agentwerkstatt.services.tool_executor import ToolExecutor
# from agentwerkstatt.tools.base import BaseTool
# from agentwerkstatt.tools.discovery import ToolRegistry


# class StaticTool(BaseTool):
#     def get_name(self) -> str:
#         return "static_tool"

#     def get_description(self) -> str:
#         return "A simple tool that returns a fixed value."

#     def get_schema(self) -> dict[str, Any]:
#         return {
#             "name": self.get_name(),
#             "description": self.get_description(),
#             "input_schema": {"type": "object", "properties": {}, "required": []},
#         }

#     def execute(self, **kwargs) -> dict[str, Any]:
#         return {"result": "static tool output"}


# class TestAgentEndToEnd(unittest.TestCase):
#     def setUp(self):
#         self.test_dir = Path(__file__).parent
#         self.temp_dir = tempfile.TemporaryDirectory()
#         self.tools_dir = Path(self.temp_dir.name) / "temp_tools"
#         self.tools_dir.mkdir()

#         # Create a dummy config file
#         self.config_data = {
#             "llm": {"provider": "claude", "model": "mock-model"},
#             "tools_dir": str(self.tools_dir),
#         }
#         self.config_file = Path(self.temp_dir.name) / "test_config.yaml"
#         with open(self.config_file, "w") as f:
#             yaml.dump(self.config_data, f)

#     def tearDown(self):
#         self.temp_dir.cleanup()

#     def test_agent_with_static_tool(self):
#         # 1. Setup
#         tools = [StaticTool()]
#         mock_llm = MockLLM(tools=tools)
#         tool_registry = ToolRegistry(tools_dir=str(self.tools_dir))
#         tool_registry._tools = tools
#         tool_registry._tool_map = {tool.get_name(): tool for tool in tools}
#         mock_observability = Mock()
#         tool_executor = ToolExecutor(tool_registry, mock_observability)
#         mock_memory_service = Mock()
#         mock_memory_service.is_enabled = False

#         agent_config = AgentConfig.from_yaml(str(self.config_file))

#         agent = Agent(
#             config=agent_config,
#             llm=mock_llm,
#             memory_service=mock_memory_service,
#             observability_service=mock_observability,
#             tool_executor=tool_executor,
#         )
#         agent.tool_registry._tools = tools
#         mock_llm.tools = tools

#         # 2. Execution
#         prompt = "Use the static tool"
#         response = agent.process_request(prompt)

#         # 3. Assertion
#         self.assertIn("static tool output", response)

#     def test_agent_persona_in_system_prompt(self):
#         """Test that the persona from test_agent.md is properly loaded and used"""
#         # 1. Setup
#         agent_config = AgentConfig.from_yaml(str(self.config_file))

#         # 2. Verification
#         default_persona = next((p for p in agent_config.personas if p.id == "default"), None)
#         self.assertIsNotNone(default_persona)
#         persona_content = default_persona.file
#         self.assertIn("TestBot", persona_content)
#         self.assertIn("Testing Assistant", persona_content)
#         self.assertIn("simple, direct testing agent", persona_content)
#         self.assertIn("test execution, tool validation", persona_content)


# if __name__ == "__main__":
#     unittest.main()
