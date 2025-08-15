import unittest
from unittest.mock import MagicMock, patch

from agentwerkstatt.llms.claude import ClaudeLLM


class TestClaudeLLM(unittest.TestCase):
    def setUp(self):
        self.mock_observability_service = MagicMock()
        with unittest.mock.patch("os.getenv", return_value="test_key"):
            self.llm = ClaudeLLM(
                persona="test_persona",
                model_name="test_model",
                tools=[],
                observability_service=self.mock_observability_service,
            )
        self.llm.api_client = MagicMock()

    def test_make_api_request_success(self):
        self.llm.api_client.post.return_value = {"content": "response"}
        result = self.llm.make_api_request([{"role": "user", "content": "hello"}])
        self.assertEqual(result, {"content": "response"})
        self.mock_observability_service.observe_llm_call.assert_called_once()
        self.mock_observability_service.update_llm_observation.assert_called_once()

    def test_make_api_request_no_messages(self):
        result = self.llm.make_api_request([])
        self.assertEqual(result, {"error": "No messages provided."})

    @patch("agentwerkstatt.llms.claude.ClaudeLLM.make_api_request")
    def test_process_request_success(self, mock_make_api_request):
        mock_make_api_request.return_value = {"content": ["response"]}
        messages, content = self.llm.process_request([{"role": "user", "content": "hello"}])
        self.assertEqual(content, ["response"])

    @patch("agentwerkstatt.llms.claude.ClaudeLLM.make_api_request")
    def test_process_request_error(self, mock_make_api_request):
        mock_make_api_request.return_value = {"error": "api error"}
        messages, content = self.llm.process_request([{"role": "user", "content": "hello"}])
        self.assertEqual(content, [{"type": "text", "text": "Error: api error"}])


if __name__ == "__main__":
    unittest.main()
