#!/usr/bin/env python3
"""
Test script to verify Langfuse connection to local docker container
"""

import os

from agent import Agent, AgentConfig


def test_langfuse_connection():
    """Test Langfuse connection and trace creation"""

    print("🧪 Testing Langfuse Local Connection")
    print("=" * 50)

    # Check if Langfuse is available
    try:
        import langfuse
    except ImportError:
        print("❌ Langfuse is not installed!")
        print("   Install with: uv sync --extra tracing")
        print("   Or: pip install langfuse>=2.50.0")
        return False

    # Check environment variables
    required_vars = [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
        "ANTHROPIC_API_KEY",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("\nPlease set:")
        for var in missing_vars:
            print(f"  export {var}='your_value_here'")
        return False

    print("✅ Environment variables found:")
    print(f"  LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST')}")
    print(f"  LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY')[:10]}...")
    print(f"  ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY')[:10]}...")

    # Test direct Langfuse connection
    try:
        from langfuse import Langfuse

        print(f"\n🔗 Testing direct connection to {os.getenv('LANGFUSE_HOST')}...")

        langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
        )

        auth_result = langfuse.auth_check()
        if auth_result:
            print("✅ Direct Langfuse connection successful!")
        else:
            print("❌ Direct Langfuse connection failed!")
            return False

    except Exception as e:
        print(f"❌ Error connecting to Langfuse: {e}")
        return False

    # Test agent initialization
    try:
        print("\n🤖 Testing Agent initialization...")
        config = AgentConfig.from_yaml("agent_config.yaml")

        # Debug config parsing
        print("📋 Config debug:")
        print(f"  langfuse_enabled: {config.langfuse_enabled}")
        print(f"  langfuse_project_name: {config.langfuse_project_name}")
        print(f"  verbose: {config.verbose}")

        agent = Agent(config)

        if agent.langfuse_enabled:
            print("✅ Agent Langfuse integration enabled!")
        else:
            print("❌ Agent Langfuse integration not enabled!")
            print("🔍 Checking what went wrong in agent setup...")
            return False

    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return False

    # Test creating a simple trace
    try:
        print("\n📊 Testing trace creation...")
        response = agent.process_request("Hello, this is a test message for Langfuse tracing.")
        print(f"🤖 Agent response: {response[:100]}...")

        # Flush traces
        print("\n📤 Flushing traces...")
        agent.flush_langfuse_traces()
        print("✅ Traces flushed!")

    except Exception as e:
        print(f"❌ Error creating trace: {e}")
        return False

    print("\n🎉 All tests passed!")
    print(f"\n👀 Check your Langfuse dashboard at: {os.getenv('LANGFUSE_HOST')}")
    print("   Navigate to 'Traces' to see your test trace.")

    return True


if __name__ == "__main__":
    test_langfuse_connection()
