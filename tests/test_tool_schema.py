"""
Unit tests for the tools module
"""

from agentwerkstatt.tools.schemas import InputSchema, InputProperty, ToolSchema


CLAUDE_SCHEMA_EXAMPLE = {
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            }
        },
        "required": ["location"],
    },
}


OPENAI_SCHEMA_EXAMPLE = {
    "type": "function",
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            }
        },
        "required": ["location"],
    },
}


class TestToolSchema:
    """Test cases for the ToolSchema class."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_to_claude_schema(self):
        """Test that the to_claude_schema method converts a ToolSchema to a Claude schema."""
        tool_schema = ToolSchema(
            name="get_weather",
            description="Get the current weather in a given location",
            input_schema=InputSchema(
                properties={
                    "location": InputProperty(
                        type="string", description="The city and state, e.g. San Francisco, CA"
                    )
                },
                required=["location"],
            ),
        )
        claude_schema = tool_schema.to_claude_schema()
        assert claude_schema == CLAUDE_SCHEMA_EXAMPLE

    def test_to_openai_schema(self):
        """Test that the to_openai_schema method converts a ToolSchema to an OpenAI schema."""
        tool_schema = ToolSchema(
            name="get_weather",
            description="Get the current weather in a given location",
            input_schema=InputSchema(
                properties={
                    "location": InputProperty(
                        type="string", description="The city and state, e.g. San Francisco, CA"
                    )
                },
                required=["location"],
            ),
        )
        openai_schema = tool_schema.to_openai_schema()
        assert openai_schema == OPENAI_SCHEMA_EXAMPLE
