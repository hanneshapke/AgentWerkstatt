from typing import Any

from agentwerkstatt.llms.base import BaseLLM
from agentwerkstatt.tools.base import BaseTool


class PlannerTool(BaseTool):
    """A tool to create a step-by-step plan to achieve a goal."""

    def __init__(self, llm_client: BaseLLM):
        self._llm_client = llm_client

    def get_name(self) -> str:
        """Returns the programmatic name of the tool."""
        return "planner"

    def get_description(self) -> str:
        """Returns a human-readable description of what the tool does."""
        return """
            Creates a step-by-step plan to achieve a goal.
            Use it to break down complex tasks into smaller, manageable steps.
            Use it as the first step in your execution process.
            """.strip()

    def get_schema(self) -> dict[str, Any]:
        """Returns the JSON schema for the tool's inputs."""
        return {
            "type": "function",
            "function": {
                "name": self.get_name(),
                "description": self.get_description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "The goal to be achieved.",
                        }
                    },
                    "required": ["goal"],
                },
            },
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Executes the tool with the given keyword arguments."""
        goal = kwargs.get("goal")
        if not goal:
            return {"error": "Goal must be provided."}

        prompt = f"Create a step-by-step plan to achieve the following goal: {goal}"
        try:
            plan = self._llm_client.query(prompt=prompt, context="")
            return {"plan": plan}
        except Exception as e:
            return {"error": f"Failed to generate plan: {e}"}
