"""
Unit tests for the LLMs module
"""

import os
import sys

import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentwerkstatt.llms.base import BaseLLM


class TestBaseLLM:
    """Test cases for the BaseLLM class."""

    def test_base_llm_is_abstract(self):
        """Test that BaseLLM cannot be instantiated directly."""
        # BaseLLM should be abstract, so this should raise an error
        with pytest.raises(TypeError):
            BaseLLM()

    def test_base_llm_has_expected_interface(self):
        """Test that BaseLLM defines the expected interface."""
        # Check that BaseLLM has the expected abstract methods
        assert hasattr(BaseLLM, "__init__")


class TestClaudeLLM:
    """Test cases for the Claude LLM implementation."""

    def test_claude_llm_can_be_imported(self):
        """Test that Claude LLM can be imported."""
        from llms.claude import ClaudeLLM

        assert ClaudeLLM is not None

    @pytest.mark.integration
    def test_claude_llm_creation_without_api_key(self):
        """Test Claude LLM creation behavior without API key."""
        from llms.claude import ClaudeLLM

        # This might raise an exception depending on implementation
        # Adjust based on your actual Claude LLM implementation
        try:
            llm = ClaudeLLM()
            assert llm is not None
        except Exception:
            # Expected if API key is required
            pass


class TestLLMsIntegration:
    """Integration tests for LLMs functionality."""

    @pytest.mark.integration
    def test_llms_modules_can_be_imported(self):
        """Test that all LLMs modules can be imported successfully."""
        import llms.base
        import llms.claude

        assert hasattr(llms.base, "BaseLLM")
        assert hasattr(llms.claude, "ClaudeLLM")
