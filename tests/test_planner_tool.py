import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from agentwerkstatt.tools.planner import PlannerTool
from agentwerkstatt.config import LLMConfig, AgentConfig


class TestPlannerTool(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tools_dir = Path(self.temp_dir.name) / "tools"
        self.tools_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_execute_success(self):
        """Test that the planner tool calls the LLM with the correct prompt."""
        # Create a mock LLM client
        mock_llm_client = MagicMock()
        # Mock the make_api_request method to return a proper response structure
        mock_llm_client.make_api_request.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": '{"plan": [{"step": 1, "task": "Do this", "tool": "some_tool", "arguments": {}}, {"step": 2, "task": "Do that", "tool": "another_tool", "arguments": {}}]}',
                }
            ]
        }
        mock_tool_registry = MagicMock()
        mock_tool_registry.get_tools.return_value = []

        agent_config = AgentConfig(
            llm=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
            tools_dir=str(self.tools_dir),
            verbose=False,
            task_objective="test goal",
        )

        # Instantiate the PlannerTool with the mock LLM client
        tool = PlannerTool(
            llm_client=mock_llm_client, tool_registry=mock_tool_registry, agent_config=agent_config
        )

        # Execute the tool
        goal = "test goal"
        result = tool.execute(goal=goal)

        # Assert that the LLM's make_api_request method was called
        mock_llm_client.make_api_request.assert_called_once()

        # Assert that the result is the plan list (not wrapped in a dict)
        expected_plan = [
            {"step": 1, "task": "Do this", "tool": "some_tool", "arguments": {}},
            {"step": 2, "task": "Do that", "tool": "another_tool", "arguments": {}},
        ]
        self.assertEqual(result, expected_plan)

    def test_execute_no_goal(self):
        """Test that the planner tool returns an error if no goal is provided."""
        # Create a mock LLM client
        mock_llm_client = MagicMock()
        mock_tool_registry = MagicMock()

        # Instantiate the PlannerTool with the mock LLM client
        tool = PlannerTool(
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry,
            agent_config=AgentConfig(
                llm=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
                tools_dir=str(self.tools_dir),
                verbose=False,
                task_objective="test goal",
            ),
        )

        # Execute the tool without a goal
        result = tool.execute()

        # Assert that an error is returned
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Goal must be provided.")

    def test_get_name(self):
        """Test get_name method"""
        mock_tool_registry = MagicMock()

        tool = PlannerTool(
            llm_client=MagicMock(),
            tool_registry=mock_tool_registry,
            agent_config=AgentConfig(
                llm=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
                tools_dir=str(self.tools_dir),
                verbose=False,
                task_objective="test goal",
            ),
        )
        self.assertEqual(tool.get_name(), "planner")

    def test_get_description(self):
        """Test get_description method"""
        mock_tool_registry = MagicMock()
        tool = PlannerTool(
            llm_client=MagicMock(),
            tool_registry=mock_tool_registry,
            agent_config=AgentConfig(
                llm=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
                tools_dir=str(self.tools_dir),
                verbose=False,
                task_objective="test goal",
            ),
        )
        description = tool.get_description()
        self.assertIn("creates a step-by-step plan", description.lower())

    def test_get_schema(self):
        """Test get_schema method"""
        mock_tool_registry = MagicMock()
        tool = PlannerTool(
            llm_client=MagicMock(),
            tool_registry=mock_tool_registry,
            agent_config=AgentConfig(
                llm=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
                tools_dir=str(self.tools_dir),
                verbose=False,
                task_objective="test goal",
            ),
        )
        schema = tool.get_schema()
        self.assertEqual(schema.name, "planner")
        # Check that the schema has the expected structure
        self.assertIn("goal", schema.input_schema.properties)
        # Convert to dict for comparison instead of comparing string to dict
        schema_dict = schema.input_schema.model_dump()
        expected_schema = {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The goal to be achieved.",
                    "default": None,
                }
            },
            "required": ["goal"],
        }
        self.assertEqual(schema_dict, expected_schema)


if __name__ == "__main__":
    unittest.main()
