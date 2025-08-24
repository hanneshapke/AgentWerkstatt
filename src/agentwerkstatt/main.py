from dataclasses import dataclass, field
from datetime import datetime
from collections.abc import Callable
from absl import logging

from .config import AgentConfig, LLMConfig

from .llms import (
    create_claude_llm,
    create_gpt_oss_llm,
    create_ollama_llm,
    create_lmstudio_llm,
    create_gemini_llm,
)
from .llms.base import BaseLLM, LLMResponse
from .tools.discovery import ToolRegistry


# Map LLM provider names to their factory functions
LLM_FACTORIES: dict[str, Callable] = {
    "claude": create_claude_llm,
    "gpt-oss": create_gpt_oss_llm,
    "ollama": create_ollama_llm,
    "lmstudio": create_lmstudio_llm,
    "gemini": create_gemini_llm,
}


@dataclass
class Message:
    """Represents a single message in a conversation."""

    role: str
    content: str


@dataclass
class Messages:
    """Represents a list of messages in a conversation."""

    messages: list[Message] = field(default_factory=list)


class Agent:
    """
    Refactored minimalistic agent with dependency injection and separation of concerns
    """

    def __init__(
        self,
        config: AgentConfig,
        # TODO: add memory and observability services
        # memory_service: MemoryServiceProtocol | None = None,
        # observability_service: ObservabilityServiceProtocol | None = None,
    ):
        self.config = config
        self.messages = Messages()

        # Corrected Initialization Order
        # 1. Initialize services without LLM or tool dependencies
        # self.memory_service = memory_service or self._create_memory_service()
        # self.observability_service = observability_service or self._create_observability_service()

        # 2. Initialize LLM, but without tools for now
        self.llm = self._create_llm()

        # 3. Initialize tool registry, injecting the LLM and config
        self.tool_registry = ToolRegistry(
            tools_dir=config.tools_dir, llm_client=self.llm, agent_config=self.config
        )
        self.llm.tools = self.tool_registry.get_tools()

        self._set_logging_verbosity(self.config.verbose)

        logging.debug(f"Tools: {self.llm.tools}")

        # Add system prompt to the LLM
        self.system_prompt = f"""
** Overall Goal **
You are a helpful AI assistant to assist the user with their task.

** Task Objective **
Solve the following task: ```{self.config.task_objective}```

** Tools **
You have the following tools at your disposal:
{self.llm.get_tool_descriptions()}

IMPORTANT: Make good use of the tools to solve the task and don't rely on your own, intrinsic knowledge.

** Response Format **
CRITICAL: You MUST respond ONLY with valid JSON wrapped in markdown code blocks. Do not use native tool calling syntax.

ALWAYS respond in EXACTLY this format (including the markdown code block):
```json
{{
  "reasoning": "Your thoughts about the next step",
  "tool_call": {{
    "tool": "tool_name",
    "input": {{
      "parameter1": "value1",
      "parameter2": "value2"
    }}
  }},
  "message_to_user": "Brief message to the user",
  "final_answer": ""
}}
```

If you don't need to call a tool, set "tool_call" to null:
```json
{{
  "reasoning": "Your thoughts",
  "tool_call": null,
  "message_to_user": "Your message",
  "final_answer": "Your final answer when task is complete"
}}
```

REQUIRED FIELDS:
- "reasoning": Always required - explain your thinking
- "tool_call": Either a tool call object or null
- "message_to_user": Always required - brief status update
- "final_answer": Required - empty string unless task is complete

FORBIDDEN:
- Do NOT use native tool calling syntax like [{{"type": "tool_use", ...}}]
- Do NOT add any text before or after the JSON code block
- Do NOT use markdown formatting inside JSON strings

** Final Tips **
- Always think before you act
- Start with the planning tool to break down complex tasks
- Limit web search to 5 results per search and max 5 searches total
- Use the reflection tool as the FINAL step to verify your work
- AFTER using the reflection tool, you MUST provide a final_answer (no more tool calls)
- Only provide a final_answer when the task is completely finished
- The current date and time is: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
""".strip()

        self.llm.set_system_prompt(self.system_prompt)

    def _set_logging_verbosity(self, verbose: bool):
        """Set logging verbosity based on config"""
        if verbose:
            logging.set_verbosity(logging.DEBUG)
        else:
            logging.set_verbosity(logging.WARNING)

    def _create_llm(self) -> BaseLLM:
        """Create LLM based on configuration"""
        provider = self.config.llm.provider
        if provider not in LLM_FACTORIES:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        factory = LLM_FACTORIES[provider]  # Direct access after validation
        return factory(
            model_name=self.config.llm.model,
            model_config=self.config.llm,
            observability_service=None,  # TODO: implement observability service
        )

    # TODO: add memory and observability services
    # def _create_memory_service(self) -> MemoryServiceProtocol:
    #     """Create memory service based on configuration"""
    #     if self.config.memory.enabled:
    #         return MemoryService(self.config)
    #     return NoOpMemoryService()

    # def _create_observability_service(self) -> ObservabilityServiceProtocol:
    #     """Create observability service based on configuration"""
    #     if self.config.langfuse.enabled:
    #         return LangfuseService(self.config)
    #     return NoOpObservabilityService()

    def run(self):
        """Run the agent."""
        # Set task objective as first assistant message
        iterations = 0

        self.messages.messages.append(Message(role="system", content=self.system_prompt))
        self.messages.messages.append(Message(role="assistant", content=self.config.task_objective))

        logging.debug("--------------------------------")
        logging.debug(f"Number of messages: {len(self.messages.messages)}")
        for i, message in enumerate(self.messages.messages):
            logging.debug(f"Message {i}: {message.role} - {message.content}")

        while True:
            iterations += 1
            print(f"Iteration {iterations}")
            if self.config.max_iterations and iterations > self.config.max_iterations:
                print("Max iterations reached")
                break

            response = self.llm.query(self.messages)
            # parse response as LLMResponse
            logging.debug(f"Response: {response}")
            response_json = response.model_dump_json(indent=2)
            response = LLMResponse.model_validate_json(response_json)
            logging.debug(f"Response: {response}")

            if response.tool_call:
                print(f"* Tool call: {response.tool_call.tool}")
                logging.debug(f"Tool call: {response.tool_call}")
                tool = self.tool_registry.get_tool_by_name(response.tool_call)
                logging.debug(f"Tool: {tool}")
                logging.debug(f"Tool input: {response.tool_call.input}")
                tool_response = tool.execute(**response.tool_call.input)
                logging.debug(f"Tool response: {tool_response}")
                self.messages.messages.append(
                    Message(
                        role="assistant",
                        content=f"The tool {response.tool_call.tool} exited successfully and returned the following response: {tool_response}",
                    )
                )
            elif response.final_answer:
                print(f"Final answer: {response.final_answer}")
                break
            elif response.reasoning:
                logging.debug(f"Reasoning: {response.reasoning}")
                print(f"* Message to user: {response.message_to_user}")
                self.messages.messages.append(
                    Message(role="assistant", content=f"Reasoning: {response.reasoning}")
                )
            else:
                print("No response from LLM")
                break


def main():
    config = AgentConfig(
        llm=LLMConfig(
            provider="claude",
            model="claude-sonnet-4-20250514",
        ),
        tools_dir="./src/agentwerkstatt/tools",
        verbose=False,
        max_iterations=15,
        task_objective="Find good concerts in Portland in the next 3 months and write me a short summary of the concerts as a markdown file.",
    )
    agent = Agent(config)
    agent.run()


if __name__ == "__main__":
    main()
