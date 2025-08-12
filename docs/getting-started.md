# Getting Started

This guide will help you get up and running with AgentWerkstatt quickly.

## Prerequisites

- Python 3.10 or higher
- An Anthropic API key for Claude
- (Optional) A Tavily API key for web search
- (Optional) An OpenAI API key for mem0 memory system

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hanneshapke/agentwerkstatt.git
   cd agentwerkstatt
   ```

2. **Install dependencies:**
   ```bash
   # Basic installation
   uv sync

   # With optional features
   uv sync --extra tracing  # Langfuse tracing support
   uv sync --extra memory   # mem0 memory support
   uv sync --all-extras     # All optional features
   ```

3. **Set up environment variables:**
   ```bash
   # Create a .env file
   echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env
   echo "TAVILY_API_KEY=your_tavily_api_key_here" >> .env          # Optional for web search
   echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env          # Optional for mem0 memory
   ```

## API Keys Setup

### Anthropic API Key (Required)
1. Sign up at [console.anthropic.com](https://console.anthropic.com/)
2. Generate an API key
3. Add it to your `.env` file as `ANTHROPIC_API_KEY`

### Tavily API Key (Optional, for web search)
1. Sign up at [app.tavily.com](https://app.tavily.com/)
2. Get your API key (1,000 free searches/month)
3. Add it to your `.env` file as `TAVILY_API_KEY`

### OpenAI API Key (Optional, for mem0 memory)
1. Sign up at [platform.openai.com](https://platform.openai.com/)
2. Generate an API key
3. Add it to your `.env` file as `OPENAI_API_KEY`

## 3rd Party Services (Optional)

AgentWerkstatt includes a Docker Compose stack with integrated services:

- **mem0** - AI memory management system for persistent context
- **Langfuse** - Observability and tracing platform
- **PostgreSQL** - Database with pgvector for embeddings
- **Neo4j** - Graph database for memory relationships
- **Redis** - Caching and session storage
- **MinIO** - S3-compatible object storage

To start the services:

```bash
# Start all services
docker compose -f third_party/docker-compose.yaml up -d

# Or start specific services
docker compose -f third_party/docker-compose.yaml up -d mem0 neo4j postgres
```

For detailed setup instructions, see:
- [MEM0_SETUP.md](../third_party/MEM0_SETUP.md) - Memory system setup
- [LANGFUSE_SETUP.md](../third_party/LANGFUSE_SETUP.md) - Observability setup
- [LANGFUSE_INTEGRATION.md](../third_party/LANGFUSE_INTEGRATION.md) - Integration guide

## Basic Usage

### Command Line Interface

Run the interactive CLI:

```bash
# Using default configuration (config.yaml)
python agent.py

# Using a custom configuration file
python agent.py --config /path/to/your/config.yaml
```

Example conversation:
```
🤖 AgentWerkstatt
==================================================
Loading config from: config.yaml

I'm an example AgentWerkstatt assistant with web search capabilities!
Ask me to search the web for information.
Commands: 'quit'/'exit' to quit, 'clear' to reset, 'status' to check conversation state.

You: What's the latest news about AI developments?
🤔 Agent is thinking...

🤖 Agent: I'll search for the latest AI developments for you.

[Search results and AI summary will be displayed here]

You: clear  # Clears conversation history
🧹 Conversation history cleared!

You: quit
👋 Goodbye!
```

### Programmatic Usage

```python
from agentwerkstatt import Agent, AgentConfig

# Initialize with default config
config = AgentConfig.from_yaml("config.yaml")
agent = Agent(config)

# Or customize the configuration
config = AgentConfig(
    model="claude-sonnet-4-20250514",
    tools_dir="./tools",
    verbose=True,
    agent_objective="You are a helpful assistant with web search capabilities."
)
agent = Agent(config)

# Process a request
response = agent.process_request("Search for recent Python releases")
print(response)

# Clear conversation history
agent.llm.clear_history()
```

### Command Line Options

The CLI supports the following command line arguments:

- `--config` - Path to the agent configuration file (default: `config.yaml`)
- `--help` - Show help message and available options

Examples:
```bash
# Use default configuration
python agent.py

# Use custom configuration file
python agent.py --config my_custom_config.yaml

# Show help
python agent.py --help
```

## Next Steps

- Learn about the [Architecture](architecture.md) of the framework
- Configure your agent with the [Configuration Guide](configuration.md)
- Start developing with the [Development Guide](development.md)
- Explore the [API Reference](api-reference.md)
