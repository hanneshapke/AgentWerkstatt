import unittest
from unittest.mock import MagicMock, patch
import os

from agentwerkstatt.config import AgentConfig
from agentwerkstatt.services.langfuse_service import (
    LangfuseService,
    NoOpObservabilityService,
    langfuse_enabled_check,
)


@patch("agentwerkstatt.services.langfuse_service.get_client")
@patch("agentwerkstatt.services.langfuse_service.Langfuse")
class TestLangfuseService(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=AgentConfig)
        self.mock_config.langfuse_enabled = True

    def test_initialization_success(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client

        service = LangfuseService(self.mock_config)
        self.assertTrue(service.is_enabled)

    @patch("agentwerkstatt.services.langfuse_service.LANGFUSE_AVAILABLE", False)
    def test_initialization_langfuse_not_available(self, mock_langfuse, mock_get_client):
        service = LangfuseService(self.mock_config)
        self.assertFalse(service.is_enabled)

    def test_initialization_missing_env_vars(self, mock_langfuse, mock_get_client):
        with patch.dict("os.environ", {"LANGFUSE_PUBLIC_KEY": ""}):
            service = LangfuseService(self.mock_config)
            self.assertFalse(service.is_enabled)

    def test_observe_request(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        service.observe_request("test input", {})
        mock_client.start_span.assert_called_once()

    def test_observe_tool_execution(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)
        service._current_span = MagicMock()

        service.observe_tool_execution("test_tool", {})
        service._current_span.start_generation.assert_called_once()

    def test_update_tool_observation(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)
        mock_generation = MagicMock()

        service.update_tool_observation(mock_generation, "output")
        mock_generation.update.assert_called_once_with(output="output")
        mock_generation.end.assert_called_once()

    def test_observe_llm_call(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)
        service._current_span = MagicMock()

        service.observe_llm_call("test_model", [])
        service._current_span.start_generation.assert_called_once()

    def test_update_llm_observation(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)
        mock_generation = MagicMock()

        service.update_llm_observation(mock_generation, "output")
        mock_generation.update.assert_called_once()
        mock_generation.end.assert_called_once()

    def test_update_observation(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        # Set up a mock span to simulate active observation
        mock_span = MagicMock()
        service._current_span = mock_span

        service.update_observation("output")
        mock_span.update.assert_called_once_with(output="output")
        mock_span.update_trace.assert_called_once_with(output="output")
        mock_span.end.assert_called_once()

    def test_flush_traces(self, mock_langfuse, mock_get_client):
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        service.flush_traces()
        mock_client.flush.assert_called_once()

    def test_setup_client_auth_failure(self, mock_langfuse, mock_get_client):
        """Test setup client with authentication failure"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = False
        mock_get_client.return_value = mock_client

        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "test", "LANGFUSE_SECRET_KEY": "test"}):
            service = LangfuseService(self.mock_config)
            # Should be disabled due to auth failure
            self.assertFalse(service.is_enabled)

    @patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "", "LANGFUSE_SECRET_KEY": ""})
    def test_initialization_empty_env_vars(self, mock_langfuse, mock_get_client):
        """Test initialization with empty environment variables"""
        service = LangfuseService(self.mock_config)
        self.assertFalse(service.is_enabled)

    def test_observe_request_exception(self, mock_langfuse, mock_get_client):
        """Test observe_request with exception"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_client.start_span.side_effect = Exception("Test error")
        mock_get_client.return_value = mock_client

        service = LangfuseService(self.mock_config)
        # Should not raise exception
        service.observe_request("test input", {})

    def test_observe_tool_execution_no_span(self, mock_langfuse, mock_get_client):
        """Test observe_tool_execution with no current span"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client

        service = LangfuseService(self.mock_config)
        service._current_span = None

        result = service.observe_tool_execution("test_tool", {})
        self.assertIsNone(result)

    def test_observe_tool_execution_exception(self, mock_langfuse, mock_get_client):
        """Test observe_tool_execution with exception"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client

        mock_span = MagicMock()
        mock_span.start_generation.side_effect = Exception("Test error")

        service = LangfuseService(self.mock_config)
        service._current_span = mock_span

        result = service.observe_tool_execution("test_tool", {})
        self.assertIsNone(result)

    def test_update_tool_observation_no_generation(self, mock_langfuse, mock_get_client):
        """Test update_tool_observation with no generation"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        # Should not raise exception
        service.update_tool_observation(None, "output")

    def test_update_tool_observation_exception(self, mock_langfuse, mock_get_client):
        """Test update_tool_observation with exception"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        mock_generation = MagicMock()
        mock_generation.update.side_effect = Exception("Test error")

        # Should not raise exception
        service.update_tool_observation(mock_generation, "output")

    def test_observe_llm_call_no_span(self, mock_langfuse, mock_get_client):
        """Test observe_llm_call with no current span"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client

        service = LangfuseService(self.mock_config)
        service._current_span = None

        result = service.observe_llm_call("test_model", [])
        self.assertIsNone(result)

    def test_observe_llm_call_exception(self, mock_langfuse, mock_get_client):
        """Test observe_llm_call with exception"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client

        mock_span = MagicMock()
        mock_span.start_generation.side_effect = Exception("Test error")

        service = LangfuseService(self.mock_config)
        service._current_span = mock_span

        result = service.observe_llm_call("test_model", [])
        self.assertIsNone(result)

    def test_update_llm_observation_no_generation(self, mock_langfuse, mock_get_client):
        """Test update_llm_observation with no generation"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        # Should not raise exception
        service.update_llm_observation(None, "output")

    def test_update_llm_observation_with_usage(self, mock_langfuse, mock_get_client):
        """Test update_llm_observation with usage data"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        mock_generation = MagicMock()
        usage_data = {"tokens": 100}

        service.update_llm_observation(mock_generation, "output", usage_data)

        mock_generation.update.assert_called_once_with(output="output", usage_details=usage_data)
        mock_generation.end.assert_called_once()

    def test_update_llm_observation_exception(self, mock_langfuse, mock_get_client):
        """Test update_llm_observation with exception"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        mock_generation = MagicMock()
        mock_generation.update.side_effect = Exception("Test error")

        # Should not raise exception
        service.update_llm_observation(mock_generation, "output")

    def test_flush_traces_exception(self, mock_langfuse, mock_get_client):
        """Test flush_traces with exception"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_client.flush.side_effect = Exception("Test error")
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        # Should not raise exception
        service.flush_traces()

    def test_get_observe_decorator_enabled(self, mock_langfuse, mock_get_client):
        """Test get_observe_decorator when enabled"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client

        with patch("agentwerkstatt.services.langfuse_service.observe") as mock_observe:
            service = LangfuseService(self.mock_config)
            service.get_observe_decorator("test_name")
            mock_observe.assert_called_once_with(name="test_name")

    def test_get_observe_decorator_disabled(self, mock_langfuse, mock_get_client):
        """Test get_observe_decorator when disabled"""
        service = LangfuseService(self.mock_config)
        service._enabled = False

        decorator = service.get_observe_decorator("test_name")

        # Test that the decorator is a no-op
        def test_func():
            return "test"

        decorated_func = decorator(test_func)
        self.assertEqual(decorated_func(), "test")

    def test_is_available(self, mock_langfuse, mock_get_client):
        """Test _is_available method"""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_get_client.return_value = mock_client
        service = LangfuseService(self.mock_config)

        # Should be available when enabled and client exists
        self.assertTrue(service._is_available())

        # Should not be available when disabled
        service._enabled = False
        self.assertFalse(service._is_available())


class TestNoOpObservabilityService(unittest.TestCase):
    """Test the no-op observability service"""

    def setUp(self):
        self.service = NoOpObservabilityService()

    def test_is_enabled(self):
        """Test is_enabled property"""
        self.assertFalse(self.service.is_enabled)

    def test_observe_request(self):
        """Test observe_request does nothing"""
        # Should not raise exception
        self.service.observe_request("test", {})

    def test_observe_tool_execution(self):
        """Test observe_tool_execution returns None"""
        result = self.service.observe_tool_execution("test_tool", {})
        self.assertIsNone(result)

    def test_update_tool_observation(self):
        """Test update_tool_observation does nothing"""
        # Should not raise exception
        self.service.update_tool_observation(None, "output")

    def test_observe_llm_call(self):
        """Test observe_llm_call returns None"""
        result = self.service.observe_llm_call("test_model", [])
        self.assertIsNone(result)

    def test_update_llm_observation(self):
        """Test update_llm_observation does nothing"""
        # Should not raise exception
        self.service.update_llm_observation(None, "output")

    def test_update_observation(self):
        """Test update_observation does nothing"""
        # Should not raise exception
        self.service.update_observation("output")

    def test_flush_traces(self):
        """Test flush_traces does nothing"""
        # Should not raise exception
        self.service.flush_traces()


class TestLangfuseEnabledCheck(unittest.TestCase):
    """Test the langfuse_enabled_check decorator"""

    def test_decorator_enabled(self):
        """Test decorator when service is enabled"""

        @langfuse_enabled_check
        def test_method(self, arg):
            return f"executed with {arg}"

        mock_service = MagicMock()
        mock_service.is_enabled = True

        result = test_method(mock_service, "test")
        self.assertEqual(result, "executed with test")

    def test_decorator_disabled(self):
        """Test decorator when service is disabled"""

        @langfuse_enabled_check
        def test_method(self, arg):
            return f"executed with {arg}"

        mock_service = MagicMock()
        mock_service.is_enabled = False

        result = test_method(mock_service, "test")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
