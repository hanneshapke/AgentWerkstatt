import unittest
from unittest.mock import MagicMock, patch

import httpx

from agentwerkstatt.llms.api_client import ApiClient


class TestApiClient(unittest.TestCase):
    def setUp(self):
        self.api_client = ApiClient("http://test.com", {"header": "value"})

    @patch("httpx.Client")
    def test_post_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "success"}
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = self.api_client.post({"payload": "data"})

        self.assertEqual(result, {"data": "success"})

    @patch("httpx.Client")
    def test_post_http_error(self, mock_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": {"message": "Not Found"}}
        mock_client.return_value.__enter__.return_value.post.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        result = self.api_client.post({"payload": "data"})

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Not Found")

    @patch("httpx.Client")
    def test_post_request_error(self, mock_client):
        mock_client.return_value.__enter__.return_value.post.side_effect = httpx.RequestError(
            "Network Error", request=MagicMock()
        )

        result = self.api_client.post({"payload": "data"})

        self.assertIn("error", result)
        self.assertIn("Network error", result["error"])


if __name__ == "__main__":
    unittest.main()
