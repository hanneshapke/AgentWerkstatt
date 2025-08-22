"""Generic tool schema definition."""

from typing import Any
from pydantic import BaseModel, Field


class InputProperty(BaseModel):
    """Represents a single property in the input schema of a tool."""

    type: str = Field(..., description="The data type of the property (e.g., 'string', 'integer').")
    description: str = Field(..., description="A description of the property.")
    default: Any = Field(None, description="An optional default value for the property.")


class InputSchema(BaseModel):
    """Represents the input schema for a tool."""

    type: str = "object"
    properties: dict[str, InputProperty] = Field(
        ..., description="A dictionary of input properties."
    )
    required: list[str] = Field(..., description="A list of required property names.")


class ToolSchema(BaseModel):
    """Represents the generic schema for a tool."""

    name: str = Field(..., description="The name of the tool.")
    description: str = Field(..., description="A description of the tool.")
    input_schema: InputSchema = Field(..., description="The input schema for the tool.")

    def to_claude_schema(self) -> dict[str, Any]:
        """
        Converts a tool schema to a Claude schema.
        Example:
        {
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
        """

        # Convert input schema with custom filtering to exclude None defaults
        input_schema_dict = self.input_schema.model_dump()

        # Remove default=None from properties
        for _, prop_data in input_schema_dict.get("properties", {}).items():
            if prop_data.get("default") is None:
                prop_data.pop("default", None)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": input_schema_dict,
        }

    def to_openai_schema(self) -> dict[str, Any]:
        """
        Converts a tool schema to an OpenAI schema.
        Example:
        {
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
            }
        }
        """
        # Convert input schema with custom filtering to exclude None defaults
        input_schema_dict = self.input_schema.model_dump()

        # Remove default=None from properties
        for _, prop_data in input_schema_dict.get("properties", {}).items():
            if prop_data.get("default") is None:
                prop_data.pop("default", None)

        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": input_schema_dict,
        }
