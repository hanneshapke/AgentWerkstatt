import httpx
from absl import logging


class ApiClient:
    """A client for making API requests."""

    def __init__(self, base_url: str, headers: dict, timeout: float = 30.0):
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout

    def post(self, payload: dict) -> dict:
        """
        Makes a POST request to the specified URL.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_details = e.response.json().get("error", {})
            error_message = error_details.get("message", e.response.text)
            logging.error(f"API Error: {error_message}", exc_info=True)
            return {"error": error_message}
        except httpx.RequestError as e:
            logging.error(f"Network error calling API: {e}", exc_info=True)
            return {"error": f"Network error: {e}"}
