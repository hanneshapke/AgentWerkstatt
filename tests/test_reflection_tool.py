import unittest
from unittest.mock import MagicMock

from agentwerkstatt.tools.reflection import ReflectionTool


class TestReflectionTool(unittest.TestCase):
    def test_execute_success(self):
        """Test that the reflection tool calls the LLM with the correct prompt."""
        # Create a mock LLM client
        mock_llm_client = MagicMock()
        mock_llm_client.query.return_value = "yes"

        # Instantiate the ReflectionTool with the mock LLM client
        tool = ReflectionTool(llm_client=mock_llm_client)

        # Execute the tool
        initial_request = "test request"
        final_answer = "test answer"
        result = tool.execute(initial_request=initial_request, final_answer=final_answer)

        # Assert that the LLM's query method was called with the correct prompt
        expected_prompt = f"""
            Does the following final answer match the initial request?
            Initial Request: {initial_request}
            Final Answer: {final_answer}
            Answer with "yes" or "no" and a brief explanation.
            """.strip()
        mock_llm_client.query.assert_called_once_with(prompt=expected_prompt, context="")

        # Assert that the result is correct
        self.assertEqual(result, {"reflection": "yes"})

    def test_execute_no_request(self):
        """Test that the reflection tool returns an error if no request is provided."""
        # Create a mock LLM client
        mock_llm_client = MagicMock()

        # Instantiate the ReflectionTool with the mock LLM client
        tool = ReflectionTool(llm_client=mock_llm_client)

        # Execute the tool without a request
        result = tool.execute(final_answer="test answer")

        # Assert that an error is returned
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Initial request and final answer must be provided.")

    def test_execute_no_answer(self):
        """Test that the reflection tool returns an error if no answer is provided."""
        # Create a mock LLM client
        mock_llm_client = MagicMock()

        # Instantiate the ReflectionTool with the mock LLM client
        tool = ReflectionTool(llm_client=mock_llm_client)

        # Execute the tool without an answer
        result = tool.execute(initial_request="test request")

        # Assert that an error is returned
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Initial request and final answer must be provided.")

    def test_get_name(self):
        """Test get_name method"""
        tool = ReflectionTool(llm_client=MagicMock())
        self.assertEqual(tool.get_name(), "reflection")

    def test_get_description(self):
        """Test get_description method"""
        tool = ReflectionTool(llm_client=MagicMock())
        description = tool.get_description()
        self.assertIn("checks if the generated final answer matches", description.lower())

    def test_get_schema(self):
        """Test get_schema method"""
        tool = ReflectionTool(llm_client=MagicMock())
        schema = tool.get_schema()
        self.assertEqual(schema["function"]["name"], "reflection")
        self.assertIn("parameters", schema["function"])
        self.assertIn("initial_request", schema["function"]["parameters"]["properties"])
        self.assertIn("final_answer", schema["function"]["parameters"]["properties"])


if __name__ == "__main__":
    unittest.main()
