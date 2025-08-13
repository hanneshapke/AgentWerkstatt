import unittest

from agentwerkstatt.agent import Agent
from agentwerkstatt.config import AgentConfig
from agentwerkstatt.interfaces import Message
from agentwerkstatt.llms.mock import MockLLM
from agentwerkstatt.services.conversation_handler import ConversationHandler
from agentwerkstatt.services.tool_executor import ToolExecutor
from agentwerkstatt.tools.base import Tool


class StaticTool(Tool):
    def __init__(self):
        super().__init__(
            name="static_tool", description="A simple tool that returns a fixed value.", schema={}
        )

    def __call__(self, **kwargs):
        return "static tool output"


class TestAgentEndToEnd(unittest.TestCase):
    def test_agent_with_static_tool(self):
        # 1. Setup
        # Mock LLM
        mock_llm = MockLLM(
            responses=[
                Message(role="assistant", content='[{"tool_name": "static_tool", "tool_code": ""}]')
            ]
        )

        # Tools
        tools = [StaticTool()]
        tool_executor = ToolExecutor(tools=tools)

        # Conversation Handler
        conversation_handler = ConversationHandler(llm=mock_llm, tool_executor=tool_executor)

        # Agent Configuration
        agent_config = AgentConfig(
            llm=mock_llm,
            conversation_handler=conversation_handler,
            tools=tools,
            memory=None,
            langfuse_service=None,
        )

        # Agent
        agent = Agent(config=agent_config)

        # 2. Execution
        prompt = "Use the static tool"
        response = agent.run(prompt)

        # 3. Assertion
        self.assertIn("static tool output", response)


if __name__ == "__main__":
    unittest.main()
