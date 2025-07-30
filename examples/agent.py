from datetime import datetime

from agentwerkstatt import Agent, AgentConfig

# Method 1: Use default configuration
config = AgentConfig.from_yaml("agent_config.yaml")  # If you have a config file
session_id = f"user-123-chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
agent = Agent(config, session_id=session_id)

# Interactive demo with agent-controlled termination
while True:
    # user_input = input("\nYou:
    user_input = "I want to go to the Caribbean. Find me a good deal for 2 people traveling in November 2025."

    print("🤔 Agent is thinking...")
    response = agent.process_request(user_input)
    print(f"🤖 Agent: {response}")

    # Check if agent wants to terminate
    if "[TASK_COMPLETE]" in response:
        print("\n✅ Agent has indicated the task is complete. Ending conversation.")
        break
