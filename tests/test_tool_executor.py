import unittest
from unittest.mock import Mock

from agentwerkstatt.services.tool_executor import ToolExecutor
from agentwerkstatt.tools.discovery import ToolRegistry
from agentwerkstatt.interfaces import ObservabilityServiceProtocol, ToolResult


class TestToolExecutor(unittest.TestCase):
    def setUp(self):
        self.mock_registry = Mock(spec=ToolRegistry)
        self.mock_observability = Mock(spec=ObservabilityServiceProtocol)
        self.mock_agent = Mock()

    def test_initialization_without_agent(self):
        """Test ToolExecutor initialization without agent"""
        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)

        self.assertEqual(tool_executor.tool_registry, self.mock_registry)
        self.assertEqual(tool_executor.observability_service, self.mock_observability)
        self.assertIsNone(tool_executor.agent)

    def test_initialization_with_agent(self):
        """Test ToolExecutor initialization with agent"""
        # Mock get_tools to return an empty list for this simple test
        self.mock_registry.get_tools.return_value = []

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability, self.mock_agent)

        self.assertEqual(tool_executor.agent, self.mock_agent)

    def test_inject_agent_into_tools_without_agent(self):
        """Test _inject_agent_into_tools when no agent is provided"""
        # Line 32-33: if not self.agent: return
        ToolExecutor(self.mock_registry, self.mock_observability, None)

        # Should not call get_tools if no agent
        self.mock_registry.get_tools.assert_not_called()

    def test_inject_agent_into_tools_with_agent(self):
        """Test _inject_agent_into_tools when agent is provided"""
        # Create mock tools, some with agent attribute, some without
        mock_tool_with_agent = Mock()
        mock_tool_with_agent.agent = None

        mock_tool_without_agent = Mock()
        # Remove agent attribute to test hasattr check
        if hasattr(mock_tool_without_agent, "agent"):
            delattr(mock_tool_without_agent, "agent")

        self.mock_registry.get_tools.return_value = [mock_tool_with_agent, mock_tool_without_agent]

        ToolExecutor(self.mock_registry, self.mock_observability, self.mock_agent)

        # Only the tool with agent attribute should have it set
        self.assertEqual(mock_tool_with_agent.agent, self.mock_agent)
        self.assertFalse(hasattr(mock_tool_without_agent, "agent"))

    def test_execute_tool_calls_no_tool_use_blocks(self):
        """Test execute_tool_calls when no tool_use blocks are present"""
        # Line 51: return [], text_parts
        assistant_message = [
            {"type": "text", "text": "Hello world"},
            {"type": "other", "content": "something else"},
        ]

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        tool_results, text_parts = tool_executor.execute_tool_calls(assistant_message)

        self.assertEqual(tool_results, [])
        self.assertEqual(text_parts, ["Hello world"])

    def test_execute_tool_calls_with_text_and_tools(self):
        """Test execute_tool_calls with both text and tool blocks"""
        mock_tool = Mock()
        mock_tool.execute.return_value = {"result": "success"}
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        assistant_message = [
            {"type": "text", "text": "Let me help you"},
            {
                "type": "tool_use",
                "id": "tool_123",
                "name": "test_tool",
                "input": {"param": "value"},
            },
            {"type": "text", "text": "Done!"},
        ]

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        tool_results, text_parts = tool_executor.execute_tool_calls(assistant_message)

        self.assertEqual(len(tool_results), 1)
        self.assertEqual(text_parts, ["Let me help you", "Done!"])

    def test_execute_single_tool_call_malformed_missing_id(self):
        """Test _execute_single_tool_call with missing tool ID"""
        # Line 66-67: malformed tool block handling
        tool_block = {
            "name": "test_tool",
            "input": {"param": "value"},
            # Missing "id"
        }

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        self.assertIsInstance(result, ToolResult)
        self.assertEqual(result.tool_use_id, "")
        self.assertEqual(result.content, "Malformed tool block")
        self.assertTrue(result.is_error)

    def test_execute_single_tool_call_malformed_missing_name(self):
        """Test _execute_single_tool_call with missing tool name"""
        # Line 66-67: malformed tool block handling
        tool_block = {
            "id": "tool_123",
            "input": {"param": "value"},
            # Missing "name"
        }

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        self.assertIsInstance(result, ToolResult)
        self.assertEqual(result.tool_use_id, "")
        self.assertEqual(result.content, "Malformed tool block")
        self.assertTrue(result.is_error)

    def test_execute_single_tool_call_tool_not_found(self):
        """Test _execute_single_tool_call when tool is not found"""
        # Line 76: raise ValueError for tool not found
        self.mock_registry.get_tool_by_name.return_value = None

        tool_block = {"id": "tool_123", "name": "nonexistent_tool", "input": {"param": "value"}}

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        self.assertIsInstance(result, ToolResult)
        self.assertEqual(result.tool_use_id, "tool_123")
        self.assertIn("Tool 'nonexistent_tool' not found", result.content)
        self.assertTrue(result.is_error)

    def test_execute_single_tool_call_invalid_input_type(self):
        """Test _execute_single_tool_call with non-dict input"""
        # Line 79-81: TypeError for non-dict input
        mock_tool = Mock()
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        tool_block = {
            "id": "tool_123",
            "name": "test_tool",
            "input": "invalid_string_input",  # Should be dict
        }

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        self.assertIsInstance(result, ToolResult)
        self.assertEqual(result.tool_use_id, "tool_123")
        self.assertIn("must be a dictionary", result.content)
        self.assertTrue(result.is_error)

    def test_execute_single_tool_call_result_conversion_dict(self):
        """Test result conversion for dict output"""
        # Line 85-86: dict conversion to JSON
        mock_tool = Mock()
        mock_tool.execute.return_value = {"key": "value", "number": 42}
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        tool_block = {"id": "tool_123", "name": "test_tool", "input": {"param": "value"}}

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        self.assertIsInstance(result, ToolResult)
        self.assertEqual(result.tool_use_id, "tool_123")
        # Should be JSON string
        self.assertEqual(result.content, '{"key": "value", "number": 42}')
        self.assertFalse(result.is_error)

    def test_execute_single_tool_call_result_conversion_list(self):
        """Test result conversion for list output"""
        # Line 85-86: list conversion to JSON
        mock_tool = Mock()
        mock_tool.execute.return_value = [1, 2, {"nested": "object"}]
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        tool_block = {"id": "tool_123", "name": "test_tool", "input": {"param": "value"}}

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        self.assertEqual(result.content, '[1, 2, {"nested": "object"}]')

    def test_execute_single_tool_call_result_conversion_other_types(self):
        """Test result conversion for other types (str, int, etc.)"""
        # Line 88: str() conversion for other types
        test_cases = [
            ("string result", "string result"),
            (42, "42"),
            (3.14, "3.14"),
            (True, "True"),
            (None, "None"),
        ]

        for tool_output, expected_content in test_cases:
            with self.subTest(tool_output=tool_output):
                mock_tool = Mock()
                mock_tool.execute.return_value = tool_output
                self.mock_registry.get_tool_by_name.return_value = mock_tool

                tool_block = {"id": "tool_123", "name": "test_tool", "input": {"param": "value"}}

                tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
                result = tool_executor._execute_single_tool_call(tool_block)

                self.assertEqual(result.content, expected_content)

    def test_execute_single_tool_call_success_with_observability(self):
        """Test successful tool execution with observability calls"""
        mock_tool = Mock()
        mock_tool.execute.return_value = {"success": True}
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        mock_span = Mock()
        self.mock_observability.observe_tool_execution.return_value = mock_span

        tool_block = {"id": "tool_123", "name": "test_tool", "input": {"param": "value"}}

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        # Check observability calls
        self.mock_observability.observe_tool_execution.assert_called_once_with(
            "test_tool", {"param": "value"}
        )
        self.mock_observability.update_tool_observation.assert_called_once_with(
            mock_span, result.to_dict()
        )

    def test_execute_single_tool_call_exception_handling(self):
        """Test exception handling during tool execution"""
        mock_tool = Mock()
        mock_tool.execute.side_effect = ValueError("Something went wrong")
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        tool_block = {"id": "tool_123", "name": "test_tool", "input": {"param": "value"}}

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        self.assertIsInstance(result, ToolResult)
        self.assertEqual(result.tool_use_id, "tool_123")
        self.assertIn("Error in tool 'test_tool'", result.content)
        self.assertIn("Something went wrong", result.content)
        self.assertTrue(result.is_error)

    def test_execute_tool_calls_mixed_content_types(self):
        """Test execute_tool_calls with mixed content types"""
        assistant_message = [
            {"type": "text", "text": "Starting task"},
            {"type": "unknown", "data": "should be ignored"},
            {"type": "tool_use", "id": "tool_1", "name": "test_tool", "input": {}},
            {"type": "text", "text": "Finishing task"},
            {"type": "image", "url": "should be ignored"},
        ]

        mock_tool = Mock()
        mock_tool.execute.return_value = "result"
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        tool_results, text_parts = tool_executor.execute_tool_calls(assistant_message)

        self.assertEqual(len(tool_results), 1)
        self.assertEqual(text_parts, ["Starting task", "Finishing task"])

    def test_execute_tool_calls_empty_input(self):
        """Test execute_tool_calls with empty input"""
        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        tool_results, text_parts = tool_executor.execute_tool_calls([])

        self.assertEqual(tool_results, [])
        self.assertEqual(text_parts, [])

    def test_tool_input_default_handling(self):
        """Test tool execution with missing input field (should default to {})"""
        mock_tool = Mock()
        mock_tool.execute.return_value = "success"
        self.mock_registry.get_tool_by_name.return_value = mock_tool

        tool_block = {
            "id": "tool_123",
            "name": "test_tool",
            # Missing "input" field
        }

        tool_executor = ToolExecutor(self.mock_registry, self.mock_observability)
        result = tool_executor._execute_single_tool_call(tool_block)

        # Should call execute with empty dict
        mock_tool.execute.assert_called_once_with()
        self.assertFalse(result.is_error)


if __name__ == "__main__":
    unittest.main()
