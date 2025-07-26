#!/usr/bin/env python3
"""
AgentWerkstatt, a minimalistic agentic framework
"""

import json
from typing import Dict
from dotenv import load_dotenv
from absl import logging

from tools import TavilySearchTool
from llms import ClaudeLLM

load_dotenv()

logging.set_verbosity(logging.INFO)

class ClaudeAgent:
    """Agent powered by Claude API"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.tools = {
            "websearch_tool": TavilySearchTool()
        }
        self.llm = ClaudeLLM(model_name=model, tools=self.tools)

    def execute_tool_call(self, tool_name: str, tool_input: Dict) -> Dict:
        """Execute a tool call"""

        logging.info(f"Executing tool call: {tool_name} with input: {tool_input}")

        if tool_name not in self.tools:
            logging.error(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}

        tool = self.tools[tool_name]
        logging.info(f"Tool: {tool}")
        logging.info(f"Tool input: {tool_input}")
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

                # Execute the tool
                result = self.execute_tool_call(tool_name, tool_input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(result)
                })

        # If there were tool calls, make another API request to get the final response
        if tool_results:
            # Add the assistant's message with tool calls
            messages = messages + [{
                "role": "assistant",
                "content": assistant_message
            }]

            # Add tool results
            messages = messages + [{
                "role": "user",
                "content": tool_results
            }]

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
            self.llm.conversation_history = messages + [{
                "role": "assistant",
                "content": final_content
            }]

            return final_text
        else:
            # No tool calls, return the text response
            response_text = " ".join(final_response_parts)

            # Update conversation history
            self.llm.conversation_history.append(user_message)
            self.llm.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return response_text

def main():
    """CLI interface for the AgentWerkstatt"""
    print("🤖 AgentWerkstatt")
    print("=" * 50)

    # Initialize the agent
    agent = ClaudeAgent()

    print("\nI'm an example AgentWerkstatt assistant with web search capabilities!")
    print("Ask me to search the web for information.")
    print("Type 'quit', 'exit', or 'clear' to manage the session.\n")

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

            if not user_input:
                continue

            print("🤔 Agent is thinking...")
            response = agent.process_request(user_input)
            print(f"\n🤖 Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
