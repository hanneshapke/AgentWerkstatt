"""
Unit tests for persona loading from MD files and system prompt generation
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from config import AgentConfig
from llms.base import BaseLLM


class TestPersonaBaseLLM(BaseLLM):
    """Test LLM class for testing system prompt generation"""

    def __init__(self, model_name: str, tools: dict, persona: str = "", observability_service=None):
        super().__init__(model_name, tools, persona, observability_service)

    def make_api_request(self, messages: list[dict] = None) -> dict:
        """Mock API request for testing"""
        return {"content": "Mock response"}

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list]:
        """Mock process request for testing"""
        return messages, ["Mock response"]


@pytest.fixture
def test_persona_content():
    """Sample persona content for testing"""
    return """# Customer Support Agent
**Name:** SupportBot
**Role:** Customer Service Specialist

**Personality & Style:**
> SupportBot is friendly, patient, and solution-oriented. It maintains a professional yet warm tone, actively listens to customer concerns, and provides clear, actionable solutions.

**Expertise & Knowledge:**
> Specializes in product knowledge, troubleshooting, billing inquiries, and escalation procedures. Expert in de-escalation techniques and customer satisfaction protocols.

**How I Help You:**
> SupportBot assists customers by resolving issues quickly and efficiently, providing accurate information about products and services, and ensuring customer satisfaction through personalized support.
"""


@pytest.fixture
def test_config_content():
    """Sample config YAML content for testing"""
    return {
        "model": "claude-3-sonnet-20240229",
        "tools_dir": "./tools",
        "verbose": False,
        "persona": "test_persona.md",
        "langfuse": {"enabled": False, "project_name": "test-project"},
        "memory": {
            "enabled": False,
            "model_name": "gpt-4o-mini",
            "server_url": "http://localhost:8000",
        },
    }


@pytest.fixture
def temp_config_files(test_persona_content, test_config_content):
    """Create temporary config and persona files for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create persona file
        persona_file = temp_path / "test_persona.md"
        persona_file.write_text(test_persona_content, encoding="utf-8")

        # Create config file
        config_file = temp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(test_config_content, f)

        yield {
            "config_path": str(config_file),
            "persona_path": str(persona_file),
            "temp_dir": str(temp_path),
        }


def test_load_persona_from_config(temp_config_files, test_persona_content):
    """Test loading persona content from MD file specified in config"""
    config = AgentConfig.from_yaml(temp_config_files["config_path"])

    # Verify config loaded correctly
    assert config.model == "claude-3-sonnet-20240229"

    # Verify persona content was loaded into persona field
    assert config.persona == test_persona_content.strip()
    assert "Customer Support Agent" in config.persona
    assert "SupportBot" in config.persona


def test_system_prompt_generation_with_persona(temp_config_files, test_persona_content):
    """Test that system prompt is correctly generated with loaded persona"""
    config = AgentConfig.from_yaml(temp_config_files["config_path"])

    # Create mock tools as a list (not dict)
    websearch_tool = Mock()
    websearch_tool.get_name.return_value = "Web Search"
    websearch_tool.get_function_name.return_value = "websearch"
    websearch_tool.description = "Search the web for information"

    calculator_tool = Mock()
    calculator_tool.get_name.return_value = "Calculator"
    calculator_tool.get_function_name.return_value = "calculator"
    calculator_tool.description = "Perform mathematical calculations"

    mock_tools = [websearch_tool, calculator_tool]

    # Create LLM with loaded persona
    llm = TestPersonaBaseLLM(model_name=config.model, tools=mock_tools, persona=config.persona)

    # Get the generated system prompt
    system_prompt = llm.persona

    # Verify persona content is in system prompt
    assert "Customer Support Agent" in system_prompt
    assert "SupportBot" in system_prompt
    assert "friendly, patient, and solution-oriented" in system_prompt


def test_custom_system_prompt_template_with_persona(temp_config_files):
    """Test custom system prompt template with loaded persona"""
    config = AgentConfig.from_yaml(temp_config_files["config_path"])

    # Create LLM with loaded persona
    llm = TestPersonaBaseLLM(model_name=config.model, tools=[], persona=config.persona)

    # The persona is the template now
    custom_prompt = llm.persona

    # Verify custom format is applied
    assert "Customer Support Agent" in custom_prompt
    assert "SupportBot" in custom_prompt


def test_fallback_to_default_persona_file():
    """Test fallback to default agent.md when persona is not specified"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create default agent.md file
        default_persona_content = "# Default Agent\nI am a helpful assistant."
        agent_md_file = temp_path / "agent.md"
        agent_md_file.write_text(default_persona_content, encoding="utf-8")

        # Create config without persona field
        config_content = {
            "model": "claude-3-sonnet-20240229",
            "tools_dir": "./tools",
            "verbose": False,
        }
        config_file = temp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_content, f)

        # Load config - should fall back to agent.md
        config = AgentConfig.from_yaml(str(config_file))

        assert config.persona == default_persona_content.strip()
        assert "Default Agent" in config.persona


def test_persona_loading_with_different_encodings(test_config_content):
    """Test persona loading with different text encodings"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create persona with special characters
        persona_content = """# International Agent
**Name:** GlobalBot 🌍
**Role:** Multilingual Assistant

**Expertise:**
> Handles queries in multiple languages: English, Español, Français, Deutsch, 中文
> Specializes in cultural sensitivity and international communication.
"""

        persona_file = temp_path / "international_persona.md"
        persona_file.write_text(persona_content, encoding="utf-8")

        test_config_content["persona"] = "international_persona.md"
        config_file = temp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(test_config_content, f)

        # Load and verify
        config = AgentConfig.from_yaml(str(config_file))

        assert "🌍" in config.persona
        assert "Español" in config.persona
        assert "中文" in config.persona


if __name__ == "__main__":
    pytest.main([__file__])
