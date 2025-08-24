from typing import Any

from .base import BaseTool
from .schemas import ToolSchema, InputSchema, InputProperty


class FileWriterTool(BaseTool):
    """A tool for writing content to a markdown file."""

    def get_name(self) -> str:
        return "file_writer"

    def get_description(self) -> str:
        return "Writes content (e.g., summaries, plans, etc.) to a markdown file, creating the file if it doesn't exist."

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.get_name(),
            description=self.get_description(),
            input_schema=InputSchema(
                properties={
                    "filename": InputProperty(
                        type="string",
                        description="The name of the markdown file to write to (e.g., 'my_file.md').",
                    ),
                    "content": InputProperty(
                        type="string",
                        description="The content to write to the file.",
                    ),
                },
                required=["filename", "content"],
            ),
        )

    def execute(self, filename: str, content: str) -> dict[str, Any]:
        """
        Executes the file writing operation.
        """
        if not filename.endswith(".md"):
            return {"error": "Filename must end with .md"}
        try:
            with open(filename, "w") as f:
                f.write(content)
            return {"success": f"Successfully wrote to {filename}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}
