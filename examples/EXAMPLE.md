# Travel Deal Assistant Example

This example demonstrates how to create a specialized AI agent using AgentWerkstatt that helps users find travel deals. The agent is configured to search for travel information and provide comprehensive recommendations.

## Overview

The example creates a travel deal assistant that:
- Uses Claude Sonnet 4 for intelligent responses
- Integrates with web search tools to find current deals
- Includes memory capabilities for context retention
- Provides Langfuse tracing for observability
- Automatically terminates conversations when tasks are complete

## Setup

### 1. Environment Configuration

Create a `.env` file (or copy from `example.env`) with your API keys:

```bash
ANTHROPIC_API_KEY="sk-..."
OPENAI_API_KEY="..."
TAVILY_API_KEY="tvly-..."
LANGFUSE_SECRET_KEY="sk-..."
LANGFUSE_PUBLIC_KEY="pk-..."
LANGFUSE_HOST="http://localhost:3000"
```

### 2. Agent Configuration

The `config.yaml` file defines the agent's behavior:

```yaml
# LLM Model Configuration
model: "claude-4-sonnet-20250514"

# Tools Configuration
tools_dir: "../tools/"

# Logging Configuration
verbose: true

# Langfuse Configuration (Optional)
langfuse:
  enabled: true
  project_name: "agentwerkstatt"

# Memory Configuration (Optional)
memory:
  enabled: true
  model_name: "gpt-4o-mini"
  server_url: "http://localhost:8000"

# Agent Objective/System Prompt
persona: |
  You are a helpful assistant that helps finding great travel deals.
  When you have successfully completed assembling a travel package, end your response with '[TASK_COMPLETE]' to indicate that the task is complete.
```

### 3. Running the Example

The example can be run with:

```bash
python agent.py
```

## Code Explanation

```python
from datetime import datetime
from agentwerkstatt import Agent, AgentConfig

# Load configuration from YAML file
config = AgentConfig.from_yaml("config.yaml")

# Create unique session ID for conversation tracking
session_id = f"user-123-chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# Initialize the agent
agent = Agent(config, session_id=session_id)

# Interactive loop with automatic termination
while True:
    user_input = "I want to go to the Caribbean. Find me a good deal for 2 people traveling in November 2025."

    print("🤔 Agent is thinking...")
    response = agent.process_request(user_input)
    print(f"🤖 Agent: {response}")

    # Check if agent wants to terminate
    if "[TASK_COMPLETE]" in response:
        print("\n✅ Agent has indicated the task is complete. Ending conversation.")
        break
```

## Features Demonstrated

- **Intelligent Web Search**: The agent uses tools to search for current travel deals
- **Structured Responses**: Provides organized information with pricing, recommendations, and booking tips
- **Automatic Termination**: Uses `[TASK_COMPLETE]` marker to end conversations naturally
- **Session Management**: Tracks conversations with unique session IDs
- **Memory Integration**: Remembers context across interactions (when enabled)
- **Observability**: Traces conversations with Langfuse for debugging and analysis

## Example Output

Here's the actual output from a recent run of this example:

```
🤖 Agent: Based on my research, I've found some excellent Caribbean deals for 2 people traveling in November 2025. Here's what I discovered:

## **Best Caribbean Travel Deals for November 2025**

### **🌟 Top Recommendations:**

**1. Dominican Republic - Punta Cana**
- **Best Overall Value**: Starting from $952 per person (down from $1,475)
- **Why November?**: Perfect weather (86°F), shoulder season pricing
- **Featured Deal**: Excellence Punta Cana (Adults Only) - All Inclusive via Expedia
- **Includes**: Flights + hotel + all meals & drinks

**2. Jamaica**
- **Budget-Friendly**: Ranked #2 in best cheap Caribbean destinations
- **November Advantage**: Hurricane season rates with great weather
- **Deals**: All-inclusive resorts with up to 50% savings
- **Popular Areas**: Montego Bay, Negril, Ocho Rios

**3. Barbados**
- **Premium Experience**: 84°F temperatures, excellent weather
- **Value**: Favorable exchange rates, great shoulder season deals
- **Perfect for**: Couples seeking luxury at reasonable prices

### **🏖️ Weather in November 2025:**
- **Temperature**: 84-86°F across most Caribbean islands
- **Conditions**: Dry season begins, minimal rainfall
- **Best Islands**: Punta Cana, Jamaica, Barbados, Aruba all at 86-30°C

### **💰 Where to Book:**
1. **Expedia**: Flight + hotel bundles, up to 100% off flights
2. **Apple Vacations**: Up to 50% savings, includes taxes & fees
3. **CheapCaribbean**: Specialized all-inclusive packages
4. **Marriott Bonvoy**: Premium all-inclusive resorts
5. **Costco Travel**: Member exclusive deals

### **🎯 My Top Package Recommendation:**
**Excellence Punta Cana (Adults Only)**
- **Price**: $952 per person (total $1,904 for 2 people)
- **Includes**: Round-trip flights, all-inclusive resort, transfers
- **Savings**: $523 per person off regular price
- **Features**: Adults-only, premium all-inclusive, beautiful beaches

### **📅 Booking Tips:**
- November is shoulder season = better prices
- Book 2-3 months in advance for best deals
- Consider travel insurance due to hurricane season proximity
- All-inclusive resorts offer best value for couples

**Total Estimated Cost for 2 People**: $1,904 - $2,400 depending on destination and resort level.

Would you like me to search for more specific deals for any particular Caribbean destination, or do you need help with booking information for any of these options?

[TASK_COMPLETE]

✅ Agent has indicated the task is complete. Ending conversation.
```

## Key Takeaways

This example showcases several important AgentWerkstatt features:

1. **Domain-Specific Agents**: The agent is specialized for travel assistance through its system prompt
2. **Tool Integration**: Automatically uses web search tools to find current information
3. **Structured Output**: Provides well-organized, actionable information
4. **Natural Termination**: Uses completion markers to end conversations appropriately
5. **Full Observability**: Tracks all interactions for debugging and improvement

## Next Steps

To customize this example:
- Modify the `persona` in the config file for different domains
- Adjust the tools directory to include custom tools
- Change the termination logic or markers
- Integrate additional services like memory or Langfuse tracing
