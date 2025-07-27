#!/usr/bin/env python3

import json
from dataclasses import dataclass

import yaml
from absl import logging

from llms.claude import ClaudeLLM
from tools.discovery import ToolRegistry


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
        # # Check for incomplete tool calls and complete them automatically
        # incomplete_info = self._get_incomplete_tool_calls()
        # if incomplete_info:
        #     print("🔄 Completing previous tool call...")
        #     try:
        #         self._complete_tool_calls(incomplete_info)
        #         print("✅ Previous tool call completed!")
        #     except Exception as e:
        #         print(f"❌ Error completing tool call: {e}")
        #         return "❌ Could not complete previous tool call. Please type 'clear' to reset the conversation history."

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

    # def _get_incomplete_tool_calls(self) -> dict | None:
    #     """
    #     Get information about incomplete tool calls in conversation history

    #     Returns:
    #         Dict with tool call info if incomplete calls exist, None otherwise
    #         Format: {
    #             'assistant_message': {...},
    #             'missing_tool_calls': [{tool_use_block}, ...]
    #         }
    #     """
    #     if not self.llm.conversation_history:
    #         return None

    #     # Look for the last assistant message
    #     last_assistant_msg = None
    #     last_assistant_idx = None
    #     for i, msg in enumerate(reversed(self.llm.conversation_history)):
    #         if msg.get("role") == "assistant":
    #             last_assistant_msg = msg
    #             last_assistant_idx = len(self.llm.conversation_history) - 1 - i
    #             break

    #     if not last_assistant_msg:
    #         return None

    #     # Check if it contains tool_use
    #     content = last_assistant_msg.get("content", [])
    #     if isinstance(content, str):
    #         return None

    #     tool_use_blocks = []
    #     for block in content:
    #         if isinstance(block, dict) and block.get("type") == "tool_use":
    #             tool_use_blocks.append(block)

    #     if not tool_use_blocks:
    #         return None

    #     # Check if there are corresponding tool_results after this assistant message
    #     completed_tool_ids = set()

    #     # Look at messages after the assistant message
    #     for msg in self.llm.conversation_history[last_assistant_idx + 1:]:
    #         if msg.get("role") == "user":
    #             user_content = msg.get("content", [])
    #             if isinstance(user_content, str):
    #                 # This is a regular user message, not tool results
    #                 break

    #             for block in user_content:
    #                 if isinstance(block, dict) and block.get("type") == "tool_result":
    #                     completed_tool_ids.add(block.get("tool_use_id"))

    #     # Find missing tool calls
    #     missing_tool_calls = []
    #     for tool_block in tool_use_blocks:
    #         if tool_block.get("id") not in completed_tool_ids:
    #             missing_tool_calls.append(tool_block)

    #     if missing_tool_calls:
    #         return {
    #             'assistant_message': last_assistant_msg,
    #             'assistant_message_idx': last_assistant_idx,
    #             'missing_tool_calls': missing_tool_calls
    #         }

    #     return None

    # def _complete_tool_calls(self, incomplete_info: dict) -> None:
    #     """
    #     Complete the missing tool calls and update conversation history

    #     Args:
    #         incomplete_info: Dict from _get_incomplete_tool_calls()
    #     """
    #     missing_tool_calls = incomplete_info['missing_tool_calls']
    #     assistant_msg_idx = incomplete_info['assistant_message_idx']

    #     # Execute missing tool calls
    #     tool_results = []
    #     for tool_block in missing_tool_calls:
    #         tool_name = tool_block["name"]
    #         tool_input = tool_block["input"]
    #         tool_id = tool_block["id"]

    #         try:
    #             result = self.execute_tool_call(tool_name, tool_input)
    #             tool_results.append({
    #                 "type": "tool_result",
    #                 "tool_use_id": tool_id,
    #                 "content": json.dumps(result)
    #             })
    #         except Exception as e:
    #             logging.error(f"Error executing tool {tool_name}: {e}")
    #             tool_results.append({
    #                 "type": "tool_result",
    #                 "tool_use_id": tool_id,
    #                 "content": f"Error: {str(e)}"
    #             })

    #     # Add tool results to conversation history
    #     tool_result_message = {"role": "user", "content": tool_results}
    #     self.llm.conversation_history.insert(assistant_msg_idx + 1, tool_result_message)

    #     # Get final response from Claude
    #     messages_for_completion = self.llm.conversation_history.copy()
    #     final_response = self.llm.make_api_request(messages_for_completion)

    #     if "error" not in final_response:
    #         final_content = final_response.get("content", [])
    #         final_assistant_msg = {"role": "assistant", "content": final_content}
    #         self.llm.conversation_history.append(final_assistant_msg)


def main():
    """CLI interface for the AgentWerkstatt"""
    print("🤖 AgentWerkstatt")
    print("=" * 50)

    config = AgentConfig.from_yaml("agent_config.yaml")

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
                # incomplete_info = agent._get_incomplete_tool_calls()
                # has_incomplete = incomplete_info is not None
                # print(f"📊 Conversation: {history_len} messages, Incomplete tools: {'Yes' if has_incomplete else 'No'}")
                # if has_incomplete:
                #     print("⚠️  Use 'clear' to reset conversation history")
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


if __name__ == "__main__":
    main()
