import unittest
from unittest.mock import MagicMock

from agentwerkstatt.tools.planner import PlannerTool


class TestPlannerTool(unittest.TestCase):
    def test_execute_success(self):
        """Test that the planner tool calls the LLM with the correct prompt."""
        # Create a mock LLM client
        mock_llm_client = MagicMock()
        mock_llm_client.query.return_value = "Step 1: Do this. Step 2: Do that."

        # Instantiate the PlannerTool with the mock LLM client
        tool = PlannerTool(llm_client=mock_llm_client)

        # Execute the tool
        goal = "test goal"
        result = tool.execute(goal=goal)

        # Assert that the LLM's query method was called with the correct prompt
        expected_prompt = f"Create a step-by-step plan to achieve the following goal: {goal}"
        mock_llm_client.query.assert_called_once_with(prompt=expected_prompt, context="")

        # Assert that the result is correct
        self.assertEqual(result, {"plan": "Step 1: Do this. Step 2: Do that."})

    def test_execute_no_goal(self):
        """Test that the planner tool returns an error if no goal is provided."""
        # Create a mock LLM client
        mock_llm_client = MagicMock()

        # Instantiate the PlannerTool with the mock LLM client
        tool = PlannerTool(llm_client=mock_llm_client)

        # Execute the tool without a goal
        result = tool.execute()

        # Assert that an error is returned
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Goal must be provided.")

    def test_get_name(self):
        """Test get_name method"""
        tool = PlannerTool(llm_client=MagicMock())
        self.assertEqual(tool.get_name(), "planner")

    def test_get_description(self):
        """Test get_description method"""
        tool = PlannerTool(llm_client=MagicMock())
        description = tool.get_description()
        self.assertIn("creates a step-by-step plan", description.lower())

    def test_get_schema(self):
        """Test get_schema method"""
        tool = PlannerTool(llm_client=MagicMock())
        schema = tool.get_schema()
        self.assertEqual(schema["function"]["name"], "planner")
        self.assertIn("parameters", schema["function"])
        self.assertIn("goal", schema["function"]["parameters"]["properties"])


if __name__ == "__main__":
    unittest.main()
