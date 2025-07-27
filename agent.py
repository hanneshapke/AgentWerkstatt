#!/usr/bin/env python3

import json
from dataclasses import dataclass

import yaml
from absl import app, flags, logging

from llms.claude import ClaudeLLM
from tools.discovery import ToolRegistry

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'config',
    'agent_config.yaml',
    'Path to the agent configuration file.'
)


@dataclass
class AgentConfig:
    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path) as f:
            return cls(**yaml.safe_load(f))

    model: str = ""
    tools_dir: str = ""
    verbose: bool = False
    agent_objective: str = ""


class Agent:
    """Minimalistic agent"""

    def __init__(self, config: AgentConfig):
        self.tool_registry = ToolRegistry(tools_dir=config.tools_dir)
        self.tools = self.tool_registry.get_tools()
        self.llm = ClaudeLLM(
            agent_objective=config.agent_objective, model_name=config.model, tools=self.tools
        )

        self._set_logging_verbosity(config.verbose)

        logging.debug(f"Tools: {self.tools}")

    def _set_logging_verbosity(self, verbose: bool):
        if verbose:
            logging.set_verbosity(logging.DEBUG)
        else:
            logging.set_verbosity(logging.ERROR)

    def execute_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """Execute a tool call"""

        tool = self.tool_registry.get_tool_by_name(tool_name)
        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return tool.execute(**tool_input)

    def process_request(self, user_input: str) -> str:
        """
        Process user request using Claude API

        Args:
            user_input: User's request as a string

        Returns:
            Response string from Claude
        """

        user_message = {"role": "user", "content": user_input}
        messages = self.llm.conversation_history + [user_message]
        messages, assistant_message = self.llm.process_request(messages)

        # Handle tool calls if present
        tool_results = []
        final_response_parts = []

        for content_block in assistant_message:
            if content_block.get("type") == "text":
                final_response_parts.append(content_block["text"])
            elif content_block.get("type") == "tool_use":
                tool_name = content_block["name"]
                tool_input = content_block["input"]
                tool_id = content_block["id"]

                try:
                    # Execute the tool
                    result = self.execute_tool_call(tool_name, tool_input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result),
                        }
                    )
                except Exception as e:
                    print(f"❌ Error executing tool {tool_name}: {e}")
                    # Add error result instead of failing completely
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error: {str(e)}",
                        }
                    )

        # If there were tool calls, make another API request to get the final response
        if tool_results:
            # Add the assistant's message with tool calls
            messages = messages + [{"role": "assistant", "content": assistant_message}]

            # Add tool results
            messages = messages + [{"role": "user", "content": tool_results}]

            # Get final response from Claude
            final_response = self.llm.make_api_request(messages)

            if "error" in final_response:
                return f"❌ Error getting final response: {final_response['error']}"

            final_content = final_response.get("content", [])
            final_text = ""
            for block in final_content:
                if block.get("type") == "text":
                    final_text += block["text"]

            # Update conversation history
            self.llm.conversation_history = messages + [
                {"role": "assistant", "content": final_content}
            ]

            return final_text
        else:
            # No tool calls, return the text response
            response_text = " ".join(final_response_parts)

            # Update conversation history
            self.llm.conversation_history.append(user_message)
            self.llm.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            return response_text


def main(argv):
    """CLI interface for the AgentWerkstatt"""
    del argv  # Unused

    print("🤖 AgentWerkstatt")
    print("=" * 50)

    print(f"Loading config from: {FLAGS.config}")

    config = AgentConfig.from_yaml(FLAGS.config)

    # Initialize the agent
    agent = Agent(config)

    print("\nI'm an example AgentWerkstatt assistant with web search capabilities!")
    print("Ask me to search the web for information.")
    print(
        "Commands: 'quit'/'exit' to quit, 'clear' to reset, 'status' to check conversation state.\n"
    )

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == "clear":
                agent.llm.clear_history()
                print("🧹 Conversation history cleared!")
                continue
            elif user_input.lower() == "status":
                history_len = len(agent.llm.conversation_history)

                print(f"📊 Conversation: {history_len} messages")
                continue

            if not user_input:
                continue

            print("🤔 Agent is thinking...")
            response = agent.process_request(user_input)
            print(f"\n🤖 Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        # except Exception as e:
        #     print(f"❌ Error: {e}")


def cli():
    """Entry point for the CLI when installed via pip"""
    app.run(main)


if __name__ == "__main__":
    app.run(main)
