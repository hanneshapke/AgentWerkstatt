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
