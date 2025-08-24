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

            Evaluate whether the final answer:
            1. Directly addresses the initial request
            2. Is complete and thorough
            3. Provides all requested deliverables

            Answer with "APPROVED" if the answer fully meets the request, or "NEEDS_REVISION" if it doesn't.
            Then provide a brief explanation of your decision.

            IMPORTANT: If you respond with "APPROVED", the agent will stop and provide this as the final answer.
            If you respond with "NEEDS_REVISION", explain what's missing or needs improvement.""".strip()
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
        schema = tool.get_schema().to_openai_schema()
        self.assertEqual(schema["name"], "reflection")
        self.assertIn("parameters", schema)
        self.assertIn("initial_request", schema["parameters"]["properties"])
        self.assertIn("final_answer", schema["parameters"]["properties"])


if __name__ == "__main__":
    unittest.main()
