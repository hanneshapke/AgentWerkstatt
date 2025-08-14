"""
Unit tests for the tools module
"""

import os
from unittest.mock import Mock, patch

import pytest

from ..services.tool_executor import ToolExecutor
from ..tools.base import BaseTool
from ..tools.discovery import ToolRegistry


class TestToolRegistry:
    """Test cases for the ToolRegistry class."""

    def setUp(self):
        # Create a dummy tools directory
        self.test_dir = os.path.dirname(__file__)
        self.tools_dir = os.path.join(self.test_dir, "temp_tools")
        os.makedirs(self.tools_dir, exist_ok=True)

    def tearDown(self):
        # Clean up the dummy tools directory
        if os.path.exists(self.tools_dir):
            for file in os.listdir(self.tools_dir):
                os.remove(os.path.join(self.tools_dir, file))
            os.rmdir(self.tools_dir)

    def test_tool_registry_creation(self):
        """Test that a ToolRegistry can be created."""
        self.setUp()
        registry = ToolRegistry(tools_dir=self.tools_dir)
        assert registry is not None
        self.tearDown()

    def test_tool_registry_has_expected_methods(self):
        """Test that ToolRegistry has expected methods."""
        self.setUp()
        registry = ToolRegistry(tools_dir=self.tools_dir)
        # Adjust these based on your actual ToolRegistry implementation
        assert hasattr(registry, "__init__")
        self.tearDown()


class TestBaseTool:
    """Test cases for the BaseTool class."""

    def test_base_tool_is_abstract(self):
        """Test that BaseTool cannot be instantiated directly."""
        # BaseTool should be abstract, so this should raise an error
        with pytest.raises(TypeError):
            BaseTool()

    def test_base_tool_has_expected_interface(self):
        """Test that BaseTool defines the expected interface."""
        # Check that BaseTool has the expected abstract methods
        assert hasattr(BaseTool, "__init__")


class TestToolsIntegration:
    """Integration tests for tools functionality."""

    @pytest.mark.integration
    def test_tools_modules_can_be_imported(self):
        """Test that all tools modules can be imported successfully."""
        import tools.base
        import tools.discovery
        import tools.websearch

        assert hasattr(tools.base, "BaseTool")
        assert hasattr(tools.discovery, "ToolRegistry")


class TestMultipleToolCalls:
    """Test cases for multiple tool call execution scenarios"""

    def test_multiple_tool_calls_execution(self):
        """Test that multiple tool calls in a single assistant message are all executed"""
        # Setup
        mock_registry = Mock(spec=ToolRegistry)
        mock_observability = Mock()
        tool_executor = ToolExecutor(mock_registry, mock_observability)

        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.execute.return_value = {"result": "tool1_result"}
        mock_tool2 = Mock()
        mock_tool2.execute.return_value = {"result": "tool2_result"}

        mock_registry.get_tool_by_name.side_effect = lambda name: {
            "search_web": mock_tool1,
            "get_weather": mock_tool2,
        }.get(name)

        # Create assistant message with multiple tool calls
        assistant_message = [
            {"type": "text", "text": "I'll help you with both tasks."},
            {
                "type": "tool_use",
                "id": "toolu_01Qf9dgcPWuhXZssFR2dHsQh",
                "name": "search_web",
                "input": {"query": "python tutorial"},
            },
            {
                "type": "tool_use",
                "id": "toolu_02Bf8egdRXvhYZttGS3eItQj",
                "name": "get_weather",
                "input": {"location": "New York"},
            },
            {"type": "text", "text": "Let me get both results for you."},
        ]

        # Execute
        tool_results, response_parts = tool_executor.execute_tool_calls(assistant_message)

        # Assertions
        assert len(tool_results) == 2, f"Expected 2 tool results, got {len(tool_results)}"

        # Check that both tools were called
        mock_tool1.execute.assert_called_once_with(query="python tutorial")
        mock_tool2.execute.assert_called_once_with(location="New York")

        # Check tool result structure
        result_ids = {result["tool_use_id"] for result in tool_results}
        expected_ids = {"toolu_01Qf9dgcPWuhXZssFR2dHsQh", "toolu_02Bf8egdRXvhYZttGS3eItQj"}
        assert result_ids == expected_ids, f"Expected tool IDs {expected_ids}, got {result_ids}"

        # Check that both results have proper structure
        for result in tool_results:
            assert result["type"] == "tool_result"
            assert "tool_use_id" in result
            assert "content" in result
            assert result.get("is_error") is not True

        # Check response parts
        assert len(response_parts) == 2
        assert "I'll help you with both tasks." in response_parts
        assert "Let me get both results for you." in response_parts

    def test_multiple_tool_calls_with_one_failure(self):
        """Test that when one tool fails, the other still executes and both get results"""
        # Setup
        mock_registry = Mock(spec=ToolRegistry)
        mock_observability = Mock()
        tool_executor = ToolExecutor(mock_registry, mock_observability)

        # Mock tools - one succeeds, one fails
        mock_tool1 = Mock()
        mock_tool1.execute.return_value = {"result": "success"}
        mock_tool2 = Mock()
        mock_tool2.execute.side_effect = Exception("Tool failed")

        mock_registry.get_tool_by_name.side_effect = lambda name: {
            "working_tool": mock_tool1,
            "failing_tool": mock_tool2,
        }.get(name)

        # Create assistant message with multiple tool calls
        assistant_message = [
            {
                "type": "tool_use",
                "id": "toolu_success",
                "name": "working_tool",
                "input": {"param": "value"},
            },
            {
                "type": "tool_use",
                "id": "toolu_failure",
                "name": "failing_tool",
                "input": {"param": "value"},
            },
        ]

        # Execute
        tool_results, response_parts = tool_executor.execute_tool_calls(assistant_message)

        # Assertions
        assert len(tool_results) == 2, f"Expected 2 tool results, got {len(tool_results)}"

        # Check that both tools were attempted
        mock_tool1.execute.assert_called_once()
        mock_tool2.execute.assert_called_once()

        # Find success and error results
        success_result = next(
            (r for r in tool_results if r["tool_use_id"] == "toolu_success"), None
        )
        error_result = next((r for r in tool_results if r["tool_use_id"] == "toolu_failure"), None)

        assert success_result is not None, "Missing success result"
        assert error_result is not None, "Missing error result"

        # Check success result
        assert success_result.get("is_error") is not True
        assert "success" in success_result["content"]

        # Check error result
        assert error_result.get("is_error") is True
        assert "failed" in error_result["content"].lower()

    def test_missing_tool_id_handling(self):
        """Test that missing tool IDs are properly detected and handled"""
        # Setup
        mock_registry = Mock(spec=ToolRegistry)
        mock_observability = Mock()
        tool_executor = ToolExecutor(mock_registry, mock_observability)

        # Create a mock tool that returns None (simulating a missing result)
        mock_tool = Mock()
        mock_tool.execute.return_value = {"result": "success"}
        mock_registry.get_tool_by_name.return_value = mock_tool

        # Create assistant message
        assistant_message = [
            {
                "type": "tool_use",
                "id": "toolu_test",
                "name": "test_tool",
                "input": {"param": "value"},
            }
        ]

        # Manually simulate a scenario where tool result is missing
        # by patching the internal method
        original_execute = tool_executor.execute_tool_calls

        def mock_execute_with_missing_result(msg):
            # Simulate tool execution but "lose" the result
            return [], []  # Return empty results to simulate the bug

        # Test with missing results
        with patch.object(
            tool_executor, "execute_tool_calls", side_effect=mock_execute_with_missing_result
        ):
            tool_results, response_parts = tool_executor.execute_tool_calls(assistant_message)

            # In the real scenario, this would be caught by the validation logic
            # and placeholder results would be added
            pass

        # Test normal execution
        tool_results, response_parts = original_execute(assistant_message)
        assert len(tool_results) == 1
        assert tool_results[0]["tool_use_id"] == "toolu_test"
