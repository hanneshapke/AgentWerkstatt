import unittest
from unittest.mock import MagicMock, patch
import httpx

from agentwerkstatt.tools.websearch import TavilySearchTool


class TestWebSearchTool(unittest.TestCase):
    @patch("agentwerkstatt.tools.websearch.httpx.Client")
    def test_execute_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"results": "search results"}
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            result = tool.execute("test query")

        self.assertEqual(result, {"results": "search results"})

    def test_execute_no_api_key(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY": ""}):
            tool = TavilySearchTool()
            result = tool.execute("test query")
            self.assertIn("error", result)

    def test_execute_no_query(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            result = tool.execute("")
            self.assertIn("error", result)

    @patch("agentwerkstatt.tools.websearch.httpx.Client")
    def test_execute_http_error(self, mock_client):
        """Test handling of HTTP errors"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        # Create an HTTPStatusError
        http_error = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )
        mock_client.return_value.__enter__.return_value.post.side_effect = http_error

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            result = tool.execute("test query")

        self.assertIn("error", result)
        self.assertIn("HTTP error 404", result["error"])

    @patch("agentwerkstatt.tools.websearch.httpx.Client")
    def test_execute_request_error(self, mock_client):
        """Test handling of network request errors"""
        request_error = httpx.RequestError("Network error")
        mock_client.return_value.__enter__.return_value.post.side_effect = request_error

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            result = tool.execute("test query")

        self.assertIn("error", result)
        self.assertIn("Network error", result["error"])

    @patch("agentwerkstatt.tools.websearch.httpx.Client")
    def test_execute_unexpected_error(self, mock_client):
        """Test handling of unexpected errors"""
        mock_client.return_value.__enter__.return_value.post.side_effect = ValueError(
            "Unexpected error"
        )

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            result = tool.execute("test query")

        self.assertIn("error", result)
        self.assertIn("An unexpected error occurred", result["error"])

    def test_get_name(self):
        """Test get_name method"""
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            self.assertEqual(tool.get_name(), "web_search")

    def test_get_description(self):
        """Test get_description method"""
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            description = tool.get_description()
            self.assertIn("searches the web", description.lower())

    def test_get_schema(self):
        """Test get_schema method"""
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()
            schema = tool.get_schema().to_claude_schema()
            self.assertEqual(schema["name"], "web_search")
            self.assertIn("input_schema", schema)
            self.assertIn("query", schema["input_schema"]["properties"])

    @patch("agentwerkstatt.tools.websearch.httpx.Client")
    def test_execute_max_results_clamping(self, mock_client):
        """Test that max_results is clamped between 1 and 20"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"results": "search results"}
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            tool = TavilySearchTool()

            # Test max_results > 20 gets clamped to 20
            tool.execute("test query", max_results=50)
            call_args = mock_client.return_value.__enter__.return_value.post.call_args
            payload = call_args[1]["json"]
            self.assertEqual(payload["max_results"], 20)

            # Test max_results < 1 gets clamped to 1
            tool.execute("test query", max_results=0)
            call_args = mock_client.return_value.__enter__.return_value.post.call_args
            payload = call_args[1]["json"]
            self.assertEqual(payload["max_results"], 1)


if __name__ == "__main__":
    unittest.main()
