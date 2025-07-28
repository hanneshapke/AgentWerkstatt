#!/usr/bin/env python3

import json
import os
from dataclasses import dataclass

import yaml
from absl import app, flags, logging

from llms.claude import ClaudeLLM
from tools.discovery import ToolRegistry

# Langfuse imports
try:
    from langfuse import get_client, observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

    # Create dummy decorators if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator if args else decorator


# mem0 imports
try:
    from mem0 import Memory

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False


FLAGS = flags.FLAGS
flags.DEFINE_string("config", "agent_config.yaml", "Path to the agent configuration file.")


@dataclass
class AgentConfig:
    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path) as f:
            data = yaml.safe_load(f)

        # Handle nested langfuse config - flatten it into the main config
        langfuse_data = data.pop("langfuse", {})
        if langfuse_data:
            data["langfuse_enabled"] = langfuse_data.get("enabled", False)
            data["langfuse_project_name"] = langfuse_data.get("project_name", "agentwerkstatt")

        # Handle nested memory config - flatten it into the main config
        memory_data = data.pop("memory", {})
        if memory_data:
            data["memory_enabled"] = memory_data.get("enabled", False)
            data["memory_model_name"] = memory_data.get("model_name", "gpt-4o-mini")
            data["memory_server_url"] = memory_data.get("server_url", "http://localhost:8000")

        return cls(**data)

    model: str = ""
    tools_dir: str = ""
    verbose: bool = False
    agent_objective: str = ""
    langfuse_enabled: bool = False
    langfuse_project_name: str = "agentwerkstatt"
    memory_enabled: bool = False
    memory_model_name: str = "gpt-4o-mini"
    memory_server_url: str = "http://localhost:8000"


class Agent:
    """Minimalistic agent"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.tool_registry = ToolRegistry(tools_dir=config.tools_dir)
        self.tools = self.tool_registry.get_tools()
        self.llm = ClaudeLLM(
            agent_objective=config.agent_objective, model_name=config.model, tools=self.tools
        )

        self._set_logging_verbosity(config.verbose)
        self._setup_langfuse(config)
        self._setup_memory(config)

        logging.debug(f"Tools: {self.tools}")

    def _setup_memory(self, config: AgentConfig):
        """Initialize mem0 if enabled and available"""
        self.memory_enabled = False
        self.memory = None

        print(f"🧠 Memory setup - MEM0_AVAILABLE: {MEM0_AVAILABLE}")
        print(f"🧠 Memory setup - config.memory_enabled: {config.memory_enabled}")

        if not MEM0_AVAILABLE:
            if config.memory_enabled:
                logging.warning(
                    "Memory is enabled in config but mem0 is not installed. Install with: pip install mem0ai"
                )
            print("❌ mem0 not available")
            return

        if not config.memory_enabled:
            logging.debug("Memory system is disabled")
            print("❌ Memory disabled in config")
            return

        try:
            # Initialize mem0 with server URL if provided
            if config.memory_server_url and config.memory_server_url != "http://localhost:8000":
                # If custom server URL is provided, use it
                self.memory = Memory(config={"server_url": config.memory_server_url})
            else:
                # Use default initialization (will use local or default server)
                self.memory = Memory()

            self.memory_enabled = True
            logging.info(
                f"mem0 memory system initialized successfully. Server: {config.memory_server_url}"
            )
            print("✅ Memory setup completed successfully!")

        except Exception as e:
            logging.error(f"Failed to initialize mem0: {e}")
            print(f"❌ Memory setup failed: {e}")
            print(
                "💡 Make sure mem0 service is running: docker compose -f 3rd_party/docker-compose.yaml up -d mem0"
            )
            return

    def _setup_langfuse(self, config: AgentConfig):
        """Initialize Langfuse if enabled and available"""
        self.langfuse_enabled = False

        print(f"🔧 Langfuse setup - LANGFUSE_AVAILABLE: {LANGFUSE_AVAILABLE}")
        print(f"🔧 Langfuse setup - config.langfuse_enabled: {config.langfuse_enabled}")

        if not LANGFUSE_AVAILABLE:
            if config.langfuse_enabled:
                logging.warning(
                    "Langfuse is enabled in config but not installed. Install with: pip install langfuse"
                )
            print("❌ Langfuse not available")
            return

        if not config.langfuse_enabled:
            logging.debug("Langfuse tracing is disabled")
            print("❌ Langfuse disabled in config")
            return

        # Check for required environment variables
        required_env_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        print(f"🔧 Checking environment variables: {required_env_vars}")
        print(f"🔧 Missing variables: {missing_vars}")

        if missing_vars:
            logging.warning(
                f"Langfuse is enabled but missing environment variables: {missing_vars}"
            )
            print(f"❌ Missing env vars: {missing_vars}")
            return

            # Initialize Langfuse client with explicit configuration (v3 API)
        try:
            from langfuse import Langfuse

            # Get host configuration
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

            # Initialize the singleton client (v3 pattern)
            Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=langfuse_host,
            )

            # Get the client instance to test connection
            self.langfuse_client = get_client()

            # Test the connection
            print("🔧 Testing authentication...")
            auth_result = self.langfuse_client.auth_check()
            print(f"🔧 Auth result: {auth_result}")
            if not auth_result:
                logging.error(
                    f"Langfuse authentication failed. Check your credentials and host: {langfuse_host}"
                )
                print("❌ Authentication failed")
                return

            self.langfuse_enabled = True
            logging.info(f"Langfuse tracing initialized successfully. Host: {langfuse_host}")
            print("✅ Langfuse setup completed successfully!")

        except Exception as e:
            logging.error(f"Failed to initialize Langfuse: {e}")
            print(f"❌ Langfuse setup failed: {e}")
            return

    def flush_langfuse_traces(self):
        """Flush any pending Langfuse traces"""
        if self.langfuse_enabled and LANGFUSE_AVAILABLE:
            try:
                if hasattr(self, "langfuse_client"):
                    self.langfuse_client.flush()
                logging.debug("Langfuse traces flushed successfully")
            except Exception as e:
                logging.error(f"Failed to flush Langfuse traces: {e}")

    def _set_logging_verbosity(self, verbose: bool):
        if verbose:
            logging.set_verbosity(logging.DEBUG)
        else:
            logging.set_verbosity(logging.ERROR)

    def _get_user_id(self) -> str:
        """Get user ID for memory operations. Can be enhanced to support multiple users."""
        return "default_user"

    def _retrieve_relevant_memories(self, user_input: str) -> str:
        """Retrieve relevant memories for the user input"""
        if not self.memory_enabled or not self.memory:
            return ""

        try:
            user_id = self._get_user_id()
            relevant_memories = self.memory.search(query=user_input, user_id=user_id, limit=3)

            if not relevant_memories.get("results"):
                return ""

            memories_str = "\n".join(
                f"- {entry['memory']}" for entry in relevant_memories["results"]
            )
            return f"\nRelevant memories:\n{memories_str}\n"

        except Exception as e:
            logging.error(f"Failed to retrieve memories: {e}")
            return ""

    def _store_conversation_memory(self, user_input: str, assistant_response: str):
        """Store the conversation in memory"""
        if not self.memory_enabled or not self.memory:
            return

        try:
            user_id = self._get_user_id()
            messages = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_response},
            ]

            self.memory.add(messages, user_id=user_id)
            logging.debug("Conversation stored in memory successfully")

        except Exception as e:
            logging.error(f"Failed to store conversation in memory: {e}")

    @observe(name="tool-execution")
    def execute_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """Execute a tool call"""

        # Update Langfuse context if enabled (v3 API)
        if self.langfuse_enabled and LANGFUSE_AVAILABLE:
            self.langfuse_client.update_current_span(
                name=f"Tool: {tool_name}", input=tool_input, metadata={"tool_name": tool_name}
            )

        tool = self.tool_registry.get_tool_by_name(tool_name)
        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        result = tool.execute(**tool_input)

        # Update with output if Langfuse is enabled (v3 API)
        if self.langfuse_enabled and LANGFUSE_AVAILABLE:
            self.langfuse_client.update_current_span(output=result)

        return result

    @observe(name="agent-request")
    def process_request(self, user_input: str) -> str:
        """
        Process user request using Claude API

        Args:
            user_input: User's request as a string

        Returns:
            Response string from Claude
        """

        # Update Langfuse context if enabled (v3 API)
        if self.langfuse_enabled and LANGFUSE_AVAILABLE:
            logging.debug("Creating Langfuse trace for agent request")
            self.langfuse_client.update_current_span(
                name="Agent Request",
                input=user_input,
                metadata={
                    "model": self.llm.model_name,
                    "project": self.config.langfuse_project_name,
                    "memory_enabled": self.memory_enabled,
                },
            )

        # Retrieve relevant memories if memory is enabled
        memory_context = self._retrieve_relevant_memories(user_input)

        # Enhance the user message with memory context if available
        enhanced_input = user_input
        if memory_context:
            enhanced_input = f"{memory_context}\nUser query: {user_input}"

        user_message = {"role": "user", "content": enhanced_input}
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

            # Store conversation in memory (using original user input, not enhanced)
            self._store_conversation_memory(user_input, final_text)

            # Update Langfuse with final output
            if self.langfuse_enabled and LANGFUSE_AVAILABLE:
                self.langfuse_client.update_current_span(output=final_text)

            return final_text
        else:
            # No tool calls, return the text response
            response_text = " ".join(final_response_parts)

            # Update conversation history (use original user_input for history, not enhanced)
            self.llm.conversation_history.append({"role": "user", "content": user_input})
            self.llm.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            # Store conversation in memory (using original user input, not enhanced)
            self._store_conversation_memory(user_input, response_text)

            # Update Langfuse with final output
            if self.langfuse_enabled and LANGFUSE_AVAILABLE:
                self.langfuse_client.update_current_span(output=response_text)

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
    if agent.memory_enabled:
        print("🧠 Memory system is active - I'll remember our conversations!")
    print("Ask me to search the web for information.")
    print(
        "Commands: 'quit'/'exit' to quit, 'clear' to reset, 'status' to check conversation state.\n"
    )

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                # Flush Langfuse traces before exit
                if agent.langfuse_enabled:
                    print("📤 Sending traces to Langfuse...")
                    agent.flush_langfuse_traces()
                    print("✅ Traces sent successfully!")
                break
            elif user_input.lower() == "clear":
                agent.llm.clear_history()
                print("🧹 Conversation history cleared!")
                continue
            elif user_input.lower() == "status":
                history_len = len(agent.llm.conversation_history)
                memory_status = "✅ Active" if agent.memory_enabled else "❌ Disabled"

                print(f"📊 Conversation: {history_len} messages")
                print(f"🧠 Memory: {memory_status}")
                continue

            if not user_input:
                continue

            print("🤔 Agent is thinking...")
            response = agent.process_request(user_input)
            print(f"\n🤖 Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            # Flush Langfuse traces before exit
            if agent.langfuse_enabled:
                print("📤 Sending traces to Langfuse...")
                agent.flush_langfuse_traces()
                print("✅ Traces sent successfully!")
            break
        # except Exception as e:
        #     print(f"❌ Error: {e}")


def cli():
    """Entry point for the CLI when installed via pip"""
    app.run(main)


if __name__ == "__main__":
    app.run(main)
