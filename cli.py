#!/usr/bin/env python3

from absl import app, flags, logging

from agent_refactored import Agent
from config import ConfigManager

FLAGS = flags.FLAGS
flags.DEFINE_string("config", "agent_config.yaml", "Path to the agent configuration file.")


def _set_logging_verbosity(verbose: bool):
    """Set logging verbosity based on config"""
    if verbose:
        logging.set_verbosity(logging.DEBUG)
    else:
        logging.set_verbosity(logging.ERROR)


def _print_welcome_message(agent: Agent):
    """Print welcome message and status"""
    print("🤖 AgentWerkstatt")
    print("=" * 50)
    print("\nI'm an example AgentWerkstatt assistant with web search capabilities!")

    if agent.memory_service.is_enabled:
        print("🧠 Memory system is active - I'll remember our conversations!")

    print("Ask me to search the web for information.")
    print(
        "Commands: 'quit'/'exit' to quit, 'clear' to reset, 'status' to check conversation state.\n"
    )


def _handle_user_command(command: str, agent: Agent) -> bool:
    """
    Handle special user commands

    Returns:
        bool: True if command was handled, False if it's a regular message
    """
    command_lower = command.lower()

    if command_lower in ["quit", "exit", "q"]:
        print("👋 Goodbye!")
        if agent.observability_service.is_enabled:
            print("📤 Sending traces to Langfuse...")
            agent.observability_service.flush_traces()
            print("✅ Traces sent successfully!")
        return True

    elif command_lower == "clear":
        agent.conversation_handler.clear_history()
        print("🧹 Conversation history cleared!")
        return True

    elif command_lower == "status":
        history_len = agent.conversation_handler.conversation_length
        memory_status = "✅ Active" if agent.memory_service.is_enabled else "❌ Disabled"
        observability_status = (
            "✅ Active" if agent.observability_service.is_enabled else "❌ Disabled"
        )

        print(f"📊 Conversation: {history_len} messages")
        print(f"🧠 Memory: {memory_status}")
        print(f"🔧 Observability: {observability_status}")
        return True

    return False


def _run_interactive_loop(agent: Agent):
    """Run the main interactive loop"""
    _print_welcome_message(agent)

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle special commands
            if _handle_user_command(user_input, agent):
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                continue

            print("🤔 Agent is thinking...")
            response = agent.process_request(user_input)
            print(f"\n🤖 Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            if agent.observability_service.is_enabled:
                print("📤 Sending traces to Langfuse...")
                agent.observability_service.flush_traces()
                print("✅ Traces sent successfully!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logging.error(f"Unexpected error in interactive loop: {e}")


def main(argv):
    """CLI interface for the AgentWerkstatt"""
    del argv  # Unused

    print(f"Loading config from: {FLAGS.config}")

    try:
        # Load and validate configuration
        config_manager = ConfigManager()
        config = config_manager.load_and_validate(FLAGS.config)

        # Set logging verbosity
        _set_logging_verbosity(config.verbose)

        # Initialize the agent
        agent = Agent(config)

        # Run interactive loop
        _run_interactive_loop(agent)

    except Exception as e:
        print(f"❌ Failed to start AgentWerkstatt: {e}")
        logging.error(f"Startup error: {e}")
        return 1

    return 0


def cli():
    """Entry point for the CLI when installed via pip"""
    app.run(main)


if __name__ == "__main__":
    app.run(main)
