import unittest
from unittest.mock import MagicMock, patch

from agentwerkstatt.config import LLMConfig
from agentwerkstatt.llms.gemini import create_gemini_llm
from agentwerkstatt.llms.generic_llm import GenericLLM


class TestGeminiLLMFactory(unittest.TestCase):
    @patch.dict("os.environ", {"GEMINI_API_KEY": "test_key"})
    def test_create_gemini_llm_success(self):
        """Test that the factory creates a GenericLLM instance with correct config."""
        mock_obs_service = MagicMock()
        llm = create_gemini_llm(
            model_name="test_model",
            tools=[],
            observability_service=mock_obs_service,
            model_config=LLMConfig(model="test_model", temperature=0.0, max_tokens=1000),
        )

        self.assertIsInstance(llm, GenericLLM)
        self.assertEqual(llm.model_name, "test_model")
        self.assertEqual(llm.observability_service, mock_obs_service)
        self.assertEqual(
            llm.api_client.base_url,
            "https://generativelanguage.googleapis.com/v1beta/models/test_model:generateContent?key=test_key",
        )
        self.assertEqual(llm.api_client.headers["Content-Type"], "application/json")

    @patch.dict("os.environ", {}, clear=True)
    def test_create_gemini_llm_missing_api_key(self):
        """Test that the factory raises a ValueError if the API key is missing."""
        with self.assertRaises(ValueError) as cm:
            create_gemini_llm(model_name="test_model")
        self.assertIn("'GEMINI_API_KEY' environment variable is required", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
