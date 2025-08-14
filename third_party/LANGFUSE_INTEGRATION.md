# Langfuse Integration for AgentWerkstatt

This document explains how to use Langfuse tracing with AgentWerkstatt for comprehensive observability of your AI agent.

## What is Langfuse?

Langfuse is an open-source observability platform for AI applications. It helps you:
- Track LLM calls, costs, and performance
- Debug agent behavior and tool usage
- Monitor conversation flows
- Evaluate agent performance over time

## Setup Instructions

### 1. Install Dependencies

Langfuse is an optional dependency. To enable tracing support:

```bash
# With uv
uv sync --extra tracing

# With pip (if installing separately)
pip install langfuse>=2.50.0
```

### 2. Get Langfuse Credentials

1. Sign up at [Langfuse Cloud](https://cloud.langfuse.com) (free tier available)
2. Create a new project or use an existing one
3. Go to **Project Settings** → **API Keys**
4. Copy your **Public Key** and **Secret Key**

### 3. Configure Environment Variables

Set the following environment variables:

```bash
# Required for Langfuse tracing
export LANGFUSE_PUBLIC_KEY="pk-lf-your_public_key_here"
export LANGFUSE_SECRET_KEY="sk-lf-your_secret_key_here"

# Choose your region
export LANGFUSE_HOST="https://cloud.langfuse.com"  # 🇪🇺 EU region
export LANGFUSE_HOST="https://us.cloud.langfuse.com"  # 🇺🇸 US region

# For self-hosted Langfuse
export LANGFUSE_HOST="http://localhost:3000"

# Required for Claude API
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### 4. Enable Tracing in Configuration

Edit your `config.yaml`:

```yaml
# Langfuse Configuration
langfuse:
  enabled: true  # Set to false to disable Langfuse tracing
  project_name: "agentwerkstatt"  # Optional: Name for organizing traces
```

## Usage

Once configured, tracing happens automatically! Every agent interaction will be logged to Langfuse with detailed information about:

### What Gets Traced

- **Agent Requests**: User input and final responses
- **LLM Calls**: Claude API requests with token usage and costs
- **Tool Executions**: Tool calls with inputs and outputs
- **Error Handling**: Failed requests and exceptions

### Example Trace Structure

```
Agent Request (user_input: "What's the weather in Tokyo?")
├── Claude Request Processing
│   └── Claude API Call (generation)
│       ├── Input: conversation messages
│       ├── Model: claude-sonnet-4-20250514
│       ├── Tokens: input=25, output=45
│       └── Output: response with tool calls
├── Tool: get_weather
│   ├── Input: {"city": "Tokyo"}
│   └── Output: {"weather": "sunny, 22°C"}
└── Claude API Call (final response generation)
    ├── Input: conversation + tool results
    ├── Tokens: input=60, output=30
    └── Output: "The weather in Tokyo is sunny with 22°C"
```

## Running with Tracing

Simply run your agent as usual:

```bash
python agent.py
```

You'll see a log message confirming Langfuse initialization:
```
INFO - Langfuse tracing initialized successfully
```

## Viewing Traces

1. Open your [Langfuse Dashboard](https://cloud.langfuse.com)
2. Navigate to **Traces** in the sidebar
3. Click on any trace to see detailed breakdown
4. Explore metrics like costs, latency, and token usage

## Advanced Features

### User Tracking

You can add user IDs and session IDs to traces by modifying the agent code:

```python
if self.langfuse_enabled and LANGFUSE_AVAILABLE:
    langfuse_context.update_current_trace(
        user_id="user_123",
        session_id="session_456",
        tags=["production", "web_search"]
    )
```

### Custom Metadata

Add custom metadata to traces:

```python
langfuse_context.update_current_observation(
    metadata={
        "environment": "production",
        "version": "1.0.0",
        "custom_field": "value"
    }
)
```

## Troubleshooting

### Common Issues

1. **"Langfuse is enabled but missing environment variables"**
   - Check that `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set
   - Verify the keys are correct in your Langfuse project settings

2. **"Langfuse is enabled in config but not installed"**
   - Run `uv sync --extra tracing` or `pip install langfuse>=2.50.0`

3. **No traces appearing in dashboard**
   - Check your environment variables
   - Verify the `LANGFUSE_HOST` matches your region/setup (e.g., `http://localhost:3000` for local docker)
   - Check network connectivity to Langfuse
   - Run the test script: `python test_langfuse_local.py`
   - Make sure to quit the agent properly (type 'quit' or Ctrl+C) to flush traces

### Disabling Tracing

To disable tracing temporarily:

```yaml
# In config.yaml
langfuse:
  enabled: false
```

Or unset environment variables:
```bash
unset LANGFUSE_PUBLIC_KEY
unset LANGFUSE_SECRET_KEY
```

## Benefits

With Langfuse integration, you get:

- **Complete visibility** into agent behavior
- **Cost tracking** for Claude API usage
- **Performance monitoring** with latency metrics
- **Debugging capabilities** for failed requests
- **Conversation analysis** for improving agent responses
- **Historical data** for performance comparisons

## Self-Hosted Langfuse

If you prefer to run Langfuse locally, follow the [docker-compose setup](./LANGFUSE_SETUP.md) in this repository, then set:

```bash
export LANGFUSE_HOST="http://localhost:3000"
```
