"""Tests for the agent module."""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import Agent, AgentConfig


class TestAgentConfig:
    """Test cases for the AgentConfig class."""

    def test_agent_config_creation(self):
        """Test that an AgentConfig can be created."""
        config = AgentConfig(
            model="claude-3-sonnet-20240229",
            tools_dir="tools",
            verbose=False,
            agent_objective="Test objective",
        )
        assert config is not None
        assert config.model == "claude-3-sonnet-20240229"

    def test_agent_config_from_yaml(self, sample_agent_config):
        """Test loading AgentConfig from YAML file."""
        # This test uses the sample_agent_config fixture
        config = AgentConfig(**sample_agent_config)
        assert config is not None


class TestAgent:
    """Test cases for the Agent class."""

    @patch("agent.ClaudeLLM")
    @patch("agent.ToolRegistry")
    def test_agent_creation(self, mock_registry, mock_llm):
        """Test that an Agent can be created with config."""
        # Mock the dependencies
        mock_registry.return_value.get_tools.return_value = []
        mock_llm.return_value = Mock()

        config = AgentConfig(
            model="claude-3-sonnet-20240229",
            tools_dir="tools",
            verbose=False,
            agent_objective="Test objective",
        )
        agent = Agent(config)
        assert agent is not None

    @patch("agent.ClaudeLLM")
    @patch("agent.ToolRegistry")
    def test_agent_has_required_attributes(self, mock_registry, mock_llm):
        """Test that Agent has the expected attributes."""
        # Mock the dependencies
        mock_registry.return_value.get_tools.return_value = []
        mock_llm.return_value = Mock()

        config = AgentConfig(
            model="claude-3-sonnet-20240229",
            tools_dir="tools",
            verbose=False,
            agent_objective="Test objective",
        )
        agent = Agent(config)
        assert hasattr(agent, "tool_registry")
        assert hasattr(agent, "tools")
        assert hasattr(agent, "llm")

    @patch("agent.ClaudeLLM")
    @patch("agent.ToolRegistry")
    def test_agent_logging_configuration(self, mock_registry, mock_llm):
        """Test that agent configures logging correctly."""
        # Mock the dependencies
        mock_registry.return_value.get_tools.return_value = []
        mock_llm.return_value = Mock()

        config = AgentConfig(
            model="claude-3-sonnet-20240229",
            tools_dir="tools",
            verbose=True,
            agent_objective="Test objective",
        )
        agent = Agent(config)
        assert agent is not None


class TestAgentIntegration:
    """Integration tests for Agent functionality."""

    @pytest.mark.integration
    def test_agent_can_be_imported(self):
        """Test that the agent module can be imported successfully."""
        import agent

        assert hasattr(agent, "Agent")
        assert hasattr(agent, "AgentConfig")

    @pytest.mark.slow
    @patch("agent.ClaudeLLM")
    @patch("agent.ToolRegistry")
    def test_agent_basic_functionality(self, mock_registry, mock_llm):
        """Test basic agent functionality (marked as slow test)."""
        # Mock the dependencies
        mock_registry.return_value.get_tools.return_value = []
        mock_llm.return_value = Mock()

        config = AgentConfig(
            model="claude-3-sonnet-20240229",
            tools_dir="tools",
            verbose=False,
            agent_objective="Test objective",
        )
        agent = Agent(config)
        assert agent is not None
        assert hasattr(agent, "execute_tool_call")
