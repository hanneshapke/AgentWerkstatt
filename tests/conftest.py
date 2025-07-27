"""Pytest configuration and fixtures."""

import pytest
import os
import sys
from unittest.mock import Mock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_environment():
    """Set up mock environment variables for testing."""
    env_vars = {
        'CLAUDE_API_KEY': 'test-claude-key',
        'TAVILY_API_KEY': 'test-tavily-key',
    }

    # Store original values
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    yield env_vars

    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def sample_agent_config():
    """Provide sample agent configuration for testing."""
    return {
        "llm": {
            "provider": "claude",
            "model": "claude-3-sonnet-20240229"
        },
        "tools": ["websearch"],
        "max_iterations": 10
    }
