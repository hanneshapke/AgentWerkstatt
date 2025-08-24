import unittest
from unittest.mock import MagicMock, patch

from agentwerkstatt.llms.claude import create_claude_llm
from agentwerkstatt.llms.generic_llm import GenericLLM
from agentwerkstatt.config import LLMConfig


class TestClaudeLLMFactory(unittest.TestCase):
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_create_claude_llm_success(self):
        """Test that the factory creates a GenericLLM instance with correct config."""
        mock_obs_service = MagicMock()
        llm = create_claude_llm(
            model_name="test_model",
            model_config=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
            tools=[],
            observability_service=mock_obs_service,
        )

        self.assertIsInstance(llm, GenericLLM)
        self.assertEqual(llm.model_name, "test_model")
        self.assertEqual(llm.observability_service, mock_obs_service)
        self.assertEqual(llm.api_client.base_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(llm.api_client.headers["x-api-key"], "test_key")

    @patch.dict("os.environ", {}, clear=True)
    def test_create_claude_llm_missing_api_key(self):
        """Test that the factory raises a ValueError if the API key is missing."""
        with self.assertRaises(ValueError) as cm:
            create_claude_llm(
                model_name="test_model",
                model_config=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
            )
        self.assertIn("'ANTHROPIC_API_KEY' environment variable is required", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
