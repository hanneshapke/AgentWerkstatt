from __future__ import annotations
from typing import Any, TYPE_CHECKING
import json

from absl import logging

from agentwerkstatt.config import AgentConfig
from agentwerkstatt.llms.base import BaseLLM
from agentwerkstatt.tools.base import BaseTool
from agentwerkstatt.tools.schemas import ToolSchema, InputSchema, InputProperty

if TYPE_CHECKING:
    from .discovery import ToolRegistry


class PlannerTool(BaseTool):
    """A tool to create a step-by-step plan to achieve a goal."""

    def __init__(
        self,
        llm_client: BaseLLM,
        tool_registry: ToolRegistry,
        agent_config: AgentConfig,
    ):
        self._llm_client = llm_client
        self._tool_registry = tool_registry
        self._agent_config = agent_config

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

    def get_schema(self) -> ToolSchema:
        """Returns the JSON schema for the tool's inputs."""
        return ToolSchema(
            name=self.get_name(),
            description=self.get_description(),
            input_schema=InputSchema(
                properties={
                    "goal": InputProperty(
                        type="string",
                        description="The goal to be achieved.",
                    ),
                },
                required=["goal"],
            ),
        )

    def execute(self, **kwargs: Any) -> dict[str, Any] | list[Any]:
        """Executes the tool with the given keyword arguments."""
        goal = kwargs.get("goal")
        if not goal:
            return {"error": "Goal must be provided."}

        # Get all tools from the registry, excluding the planner itself
        all_tools = self._tool_registry.get_tools()
        available_tools_formatted = "\n".join(
            [
                f"- {tool.get_name()}: {tool.get_description()}"
                for tool in all_tools
                if tool.get_name() != self.get_name()
            ]
        )

        prompt = f"""
You are a meticulous planner agent. Your task is to create a detailed, step-by-step plan to achieve the user's goal.
The user's goal is: "{goal}"

Make use of the following tools to achieve the goal:
{available_tools_formatted}

Please create a plan to achieve the goal. The output MUST be a single, valid JSON object containing a single key named "plan".
The "plan" key must contain an array of JSON objects, where each object represents a single step in the plan.

Each step object must have the following keys:
- "step": An integer representing the step number.
- "task": A string describing the specific task for this step.
- "tool": The exact name of the tool to use for this step (e.g., "web_search").
- "arguments": A JSON object containing the arguments to pass to the tool.

**IMPORTANT**: If the arguments for a step depend on the output of a previous step, you MUST use a placeholder string in the format `"{{result_of_step_N}}"`, where N is the step number whose output should be used.

Example of the required JSON format:
{{
  "plan": [
    {{
      "step": 1,
      "task": "Search for recent news about AI advancements.",
      "tool": "web_search",
      "arguments": {{
        "query": "latest news on AI advancements"
      }}
    }},
    {{
      "step": 2,
      "task": "Summarize the findings from the web search and save them to a file.",
      "tool": "file_writer",
      "arguments": {{
        "filename": "ai_news_summary.txt",
        "content": "{{{{result_of_step_1}}}}"
      }}
    }}
  ]
}}

Do not add any commentary or text before or after the JSON output.
"""
        # try:
        # Use make_api_request to get a structured response
        messages = [{"role": "user", "content": prompt}]
        response_data = self._llm_client.make_api_request(messages)

        if "error" in response_data:
            raise ValueError(response_data["error"])

        # Extract the text content from the response
        plan_str = response_data.get("content", [{}])[0].get("text", "")
        if not plan_str:
            raise ValueError("LLM returned an empty response.")

        # The LLM should return a list of strings in a JSON array format.
        # We attempt to parse it to ensure it's valid.
        plan_data = json.loads(plan_str)
        if "plan" not in plan_data or not isinstance(plan_data["plan"], list):
            raise ValueError("The JSON output must have a 'plan' key with a list as its value.")

        logging.debug(f"Plan: {plan_data}")
        return plan_data["plan"]
