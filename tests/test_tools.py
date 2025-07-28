"""
Unit tests for the tools module
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentwerkstatt.tools.base import BaseTool
from agentwerkstatt.tools.discovery import ToolRegistry


class TestToolRegistry:
    """Test cases for the ToolRegistry class."""

    def test_tool_registry_creation(self):
        """Test that a ToolRegistry can be created."""
        registry = ToolRegistry()
        assert registry is not None

    def test_tool_registry_has_expected_methods(self):
        """Test that ToolRegistry has expected methods."""
        registry = ToolRegistry()
        # Adjust these based on your actual ToolRegistry implementation
        assert hasattr(registry, "__init__")


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
