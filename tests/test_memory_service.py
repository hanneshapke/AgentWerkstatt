import unittest
from unittest.mock import MagicMock, patch

from agentwerkstatt.config import AgentConfig
from agentwerkstatt.services.memory_service import MemoryService, memory_enabled_check


class TestMemoryService(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=AgentConfig)
        self.mock_config.memory_enabled = True
        self.mock_config.memory_server_url = "http://test.com"

    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_initialization_success(self, mock_memory):
        service = MemoryService(self.mock_config)
        self.assertTrue(service.is_enabled)
        mock_memory.assert_called_once_with(config={"server_url": "http://test.com"})

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", False)
    def test_initialization_mem0_not_available(self):
        service = MemoryService(self.mock_config)
        self.assertFalse(service.is_enabled)

    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_retrieve_memories(self, mock_memory):
        mock_mem_instance = MagicMock()
        mock_mem_instance.search.return_value = {"results": [{"memory": "test memory"}]}
        mock_memory.return_value = mock_mem_instance
        service = MemoryService(self.mock_config)

        result = service.retrieve_memories("test input", "test_user")
        self.assertIn("test memory", result)

    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_store_conversation(self, mock_memory):
        mock_mem_instance = MagicMock()
        mock_memory.return_value = mock_mem_instance
        service = MemoryService(self.mock_config)

        service.store_conversation("user input", "assistant response", "test_user")
        mock_mem_instance.add.assert_called_once()

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", True)
    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_memory_initialization_with_default_server(self, mock_memory_class):
        """Test memory initialization with default server URL"""
        mock_config = MagicMock(spec=AgentConfig)
        mock_config.memory_enabled = True
        mock_config.memory_server_url = "http://localhost:8000"
        mock_memory = MagicMock()
        mock_memory_class.return_value = mock_memory

        with patch("builtins.print"):
            service = MemoryService(mock_config)

        # Should call Memory without config (default)
        mock_memory_class.assert_called_once_with()
        self.assertTrue(service.is_enabled)

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", True)
    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_memory_initialization_failure(self, mock_memory_class):
        """Test memory initialization failure"""
        mock_config = MagicMock(spec=AgentConfig)
        mock_config.memory_enabled = True
        mock_config.memory_server_url = "http://localhost:8000"
        mock_memory_class.side_effect = Exception("Connection failed")

        with patch("builtins.print"):  # Suppress print output
            service = MemoryService(mock_config)

        self.assertFalse(service.is_enabled)

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", True)
    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_retrieve_memories_no_results(self, mock_memory_class):
        """Test memory retrieval with no results"""
        mock_memory = MagicMock()
        mock_memory.search.return_value = {"results": []}
        mock_memory_class.return_value = mock_memory

        mock_config = MagicMock(spec=AgentConfig)
        mock_config.memory_enabled = True
        mock_config.memory_server_url = "http://localhost:8000"

        with patch("builtins.print"):
            service = MemoryService(mock_config)
        result = service.retrieve_memories("Tell me something", "user123")

        self.assertEqual(result, "")

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", True)
    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_retrieve_memories_exception(self, mock_memory_class):
        """Test memory retrieval with exception"""
        mock_memory = MagicMock()
        mock_memory.search.side_effect = Exception("Search failed")
        mock_memory_class.return_value = mock_memory

        mock_config = MagicMock(spec=AgentConfig)
        mock_config.memory_enabled = True
        mock_config.memory_server_url = "http://localhost:8000"

        with patch("builtins.print"):
            service = MemoryService(mock_config)
        result = service.retrieve_memories("Tell me something", "user123")

        self.assertEqual(result, "")

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", True)
    @patch("agentwerkstatt.services.memory_service.Memory")
    def test_store_conversation_exception(self, mock_memory_class):
        """Test conversation storage with exception"""
        mock_memory = MagicMock()
        mock_memory.add.side_effect = Exception("Store failed")
        mock_memory_class.return_value = mock_memory

        mock_config = MagicMock(spec=AgentConfig)
        mock_config.memory_enabled = True
        mock_config.memory_server_url = "http://localhost:8000"

        with patch("builtins.print"):
            service = MemoryService(mock_config)
        # Should not raise exception
        service.store_conversation("Hello", "Hi", "user123")

    def test_memory_enabled_check_decorator(self):
        """Test the memory_enabled_check decorator"""

        @memory_enabled_check
        def dummy_function(self, arg):
            return f"executed with {arg}"

        # Test with enabled memory
        mock_service = MagicMock()
        mock_service.is_enabled = True
        result = dummy_function(mock_service, "test")
        self.assertEqual(result, "executed with test")

        # Test with disabled memory
        mock_service.is_enabled = False
        result = dummy_function(mock_service, "test")
        self.assertIsNone(result)

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", False)
    def test_memory_disabled_warning(self):
        """Test warning when memory is enabled but mem0 is not available"""
        mock_config = MagicMock(spec=AgentConfig)
        mock_config.memory_enabled = True

        with patch("builtins.print"):  # Suppress print output
            with patch("agentwerkstatt.services.memory_service.logging.warning") as mock_warning:
                service = MemoryService(mock_config)
                mock_warning.assert_called_once()
                self.assertFalse(service.is_enabled)

    @patch("agentwerkstatt.services.memory_service.MEM0_AVAILABLE", True)
    def test_memory_disabled_in_config(self):
        """Test when memory is disabled in config"""
        mock_config = MagicMock(spec=AgentConfig)
        mock_config.memory_enabled = False

        with patch("builtins.print"):
            service = MemoryService(mock_config)

        self.assertFalse(service.is_enabled)


if __name__ == "__main__":
    unittest.main()
