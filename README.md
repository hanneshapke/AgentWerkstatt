<p align="center">
  <img src="https://github.com/hanneshapke/AgentWerkstatt/blob/main/misc/agent-werkstatt-logo.png?raw=true" alt="AgentWerkstatt Logo" width="400">
</p>

# AgentWerkstatt 🤖

A minimalistic agentic framework for building AI agents with tool calling capabilities.
Why do we need another agentic framework? I felt that all other frameworks were too complex and had too many dependencies, I wanted to build a framework that was easy to understand and use, and that was also easy to extend. The main goal here isn't on production scenarios (yet), but on understanding and prototyping agentic systems. Therefore, the name "AgentWerkstatt" is a play on the term Agent and the German word "Werkstatt" (workshop).

## Overview

AgentWerkstatt is a lightweight, extensible framework for creating AI agents. It is powered by Claude (Anthropic), but it is highly extensible and can be used with other LLMs. It features a modular architecture with pluggable LLM providers and tools, making it easy to build conversational agents with access to external capabilities like web search. More LLMs will be supported in the future.

## Features

- 🧠 **Modular LLM Support** - Built with extensible LLM abstraction (currently supports Claude)
- 🔧 **Tool System** - Pluggable tool architecture with automatic tool discovery
- 💬 **Conversation Management** - Built-in conversation history and context management
- 🧮 **Persistent Memory** - Optional mem0 integration for long-term memory and context retention
- 🌐 **Web Search** - Integrated Tavily API for real-time web information retrieval
- 📊 **Observability** - Optional Langfuse integration for comprehensive tracing and analytics
- 🖥️ **CLI Interface** - Ready-to-use command-line interface
- 🐳 **3rd Party Services** - Docker Compose stack with PostgreSQL, Neo4j, and other services
- ⚡ **Lightweight** - Minimal dependencies and clean architecture

## Quick Start

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key for Claude
- (Optional) A Tavily API key for web search
- (Optional) An OpenAI API key for mem0 memory system

### Installation

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

### 3rd Party Services (Optional)

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
docker compose -f 3rd_party/docker-compose.yaml up -d

# Or start specific services
docker compose -f 3rd_party/docker-compose.yaml up -d mem0 neo4j postgres
```

For detailed setup instructions, see:
- [MEM0_SETUP.md](3rd_party/MEM0_SETUP.md) - Memory system setup
- [LANGFUSE_SETUP.md](3rd_party/LANGFUSE_SETUP.md) - Observability setup
- [LANGFUSE_INTEGRATION.md](3rd_party/LANGFUSE_INTEGRATION.md) - Integration guide

### API Keys Setup

#### Anthropic API Key (Required)
1. Sign up at [console.anthropic.com](https://console.anthropic.com/)
2. Generate an API key
3. Add it to your `.env` file as `ANTHROPIC_API_KEY`

#### Tavily API Key (Optional, for web search)
1. Sign up at [app.tavily.com](https://app.tavily.com/)
2. Get your API key (1,000 free searches/month)
3. Add it to your `.env` file as `TAVILY_API_KEY`

#### OpenAI API Key (Optional, for mem0 memory)
1. Sign up at [platform.openai.com](https://platform.openai.com/)
2. Generate an API key
3. Add it to your `.env` file as `OPENAI_API_KEY`

### Usage

#### Command Line Interface

Run the interactive CLI:

```bash
# Using default configuration (agent_config.yaml)
python agent.py

# Using a custom configuration file
python agent.py --config /path/to/your/config.yaml
```

Example conversation:
```
🤖 AgentWerkstatt
==================================================
Loading config from: agent_config.yaml

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

#### Programmatic Usage

```python
from agent import Agent, AgentConfig

# Initialize with default config
config = AgentConfig.from_yaml("agent_config.yaml")
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

- `--config` - Path to the agent configuration file (default: `agent_config.yaml`)
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

## Architecture

### Core Components

```
AgentWerkstatt/
├── agent.py               # Main agent implementation and CLI
├── agent_config.yaml      # Default configuration
├── llms/                  # LLM provider modules
│   ├── base.py           # Base LLM abstraction
│   ├── claude.py         # Claude implementation
│   └── __init__.py
├── tools/                # Tool modules
│   ├── base.py          # Base tool abstraction
│   ├── discovery.py     # Automatic tool discovery
│   ├── websearch.py     # Tavily web search tool
│   └── __init__.py
├── 3rd_party/           # Third-party service integrations
│   ├── docker-compose.yaml    # Service orchestration
│   ├── Dockerfile.mem0        # Custom mem0 build
│   ├── mem0-config.yaml       # Memory system config
│   ├── MEM0_SETUP.md          # Memory setup guide
│   ├── LANGFUSE_SETUP.md      # Observability setup
│   └── LANGFUSE_INTEGRATION.md # Integration guide
└── pyproject.toml       # Project configuration
```

### LLM Providers

The framework uses a base `BaseLLM` class that can be extended for different providers:

- **Claude (Anthropic)** - Full support with tool calling
- **Future providers** - Easy to add by extending `BaseLLM`

### Tools

Tools are modular components that extend agent capabilities:

- **Web Search** - Tavily API integration for real-time information retrieval
- **Automatic Discovery** - Tools are automatically discovered from the tools directory
- **Extensible** - Add new tools by implementing `BaseTool`

### Memory System

Optional mem0 integration provides:

- **Persistent Context** - Long-term memory across conversations
- **Semantic Search** - Vector-based memory retrieval
- **Graph Relationships** - Knowledge graph storage in Neo4j
- **REST API** - Direct access to memory operations

### Agent System

The `Agent` class orchestrates:
- LLM interactions
- Tool execution and discovery
- Conversation management
- Response generation
- Memory persistence (when enabled)

## Configuration

### Environment Variables

#### Core
- `ANTHROPIC_API_KEY` - Required for Claude API access
- `TAVILY_API_KEY` - Optional, for web search functionality

#### Memory (mem0)
- `OPENAI_API_KEY` - Required for mem0 memory system (LLM and embeddings)

#### Observability (Langfuse)
- `LANGFUSE_PUBLIC_KEY` - Optional, for Langfuse tracing integration
- `LANGFUSE_SECRET_KEY` - Optional, for Langfuse tracing integration
- `LANGFUSE_HOST` - Optional, Langfuse host URL (defaults to cloud.langfuse.com)

### Configuration File

Default configuration in `agent_config.yaml`:

```yaml
# LLM Model Configuration
model: "claude-sonnet-4-20250514"

# Tools Configuration
tools_dir: "./tools"

# Logging Configuration
verbose: true

# Memory Configuration (Optional)
memory:
  enabled: false               # Set to true to enable mem0 integration
  model_name: "gpt-4o-mini"   # Model for memory processing
  server_url: "http://localhost:8000"  # mem0 server endpoint

# Langfuse Configuration (Optional)
langfuse:
  enabled: true  # Set to false to disable tracing
  project_name: "agentwerkstatt"

# Agent Objective/System Prompt
agent_objective: |
  You are a helpful assistant with web search capabilities.
  You can search the web for current information and provide accurate, helpful responses.
  Always be conversational and helpful in your responses.
```

### Memory Configuration

To enable persistent memory with mem0:

1. Install memory dependencies: `uv sync --extra memory`
2. Start the mem0 service: `docker compose -f 3rd_party/docker-compose.yaml up -d mem0`
3. Set your OpenAI API key for memory operations
4. Enable memory in your configuration:
   ```yaml
   memory:
     enabled: true
     model_name: "gpt-4o-mini"
     server_url: "http://localhost:8000"
   ```

### Model Configuration

To use a different model programmatically:

```python
config = AgentConfig(model="claude-sonnet-4-20250514")
agent = Agent(config)
```

### Observability with Langfuse

AgentWerkstatt includes optional integration with [Langfuse](https://langfuse.com) for comprehensive observability:

- **Automatic Tracing**: All agent interactions, LLM calls, and tool executions are automatically traced
- **Performance Monitoring**: Track costs, latency, and token usage
- **Debugging**: Detailed execution flow for troubleshooting
- **Analytics**: Historical data and performance insights

To enable Langfuse tracing:

1. Install the tracing dependencies: `uv sync --extra tracing`
2. Set up your Langfuse credentials (see [Environment Variables](#environment-variables))
3. Enable tracing in your configuration:
   ```yaml
   langfuse:
     enabled: true
     project_name: "your-project-name"
   ```

**Note**: Langfuse is completely optional. AgentWerkstatt works perfectly without it.

For detailed setup instructions, see [LANGFUSE_INTEGRATION.md](3rd_party/LANGFUSE_INTEGRATION.md).

## Development

### Adding a New LLM Provider

1. Create a new file in `llms/` (e.g., `openai.py`)
2. Implement the `BaseLLM` interface:

```python
from .base import BaseLLM

class OpenAILLM(BaseLLM):
    def __init__(self, model_name: str, tools: list, agent_objective: str = ""):
        super().__init__(model_name, tools, agent_objective)
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Set other provider-specific configurations

    def make_api_request(self, messages: list[dict]) -> dict:
        # Implement API request logic
        pass

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list[dict]]:
        # Implement request processing
        pass
```

3. Update `llms/__init__.py` to export the new provider

### Adding a New Tool

1. Create a new file in `tools/` (e.g., `weather.py`)
2. Implement the `BaseTool` interface:

```python
from .base import BaseTool
from typing import Any

class WeatherTool(BaseTool):
    def _get_name(self) -> str:
        return "Weather Tool"

    def _get_description(self) -> str:
        return "Get weather information for a location"

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or location name"
                    }
                },
                "required": ["location"]
            }
        }

    def execute(self, **kwargs) -> dict[str, Any]:
        # Implement tool logic
        location = kwargs.get("location")
        # Your weather API logic here
        return {"weather": f"Sunny in {location}"}
```

3. The tool will be automatically discovered by the `ToolRegistry` - no manual registration needed!

### Development Setup

```bash
# Clone and setup
git clone https://github.com/hanneshapke/agentwerkstatt.git
cd agentwerkstatt
uv sync --dev

# Code formatting and linting
uv run ruff check --fix
uv run ruff format

# Type checking
uv run mypy .

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=agentwerkstatt --cov-report=html --cov-report=term
```

### Quality Assurance

The project uses modern Python development tools:

- **Ruff** - Fast Python linter and formatter (replaces black, flake8, isort)
- **MyPy** - Static type checking
- **Pytest** - Testing framework
- **Pre-commit** - Git hooks for code quality

## Dependencies

Core dependencies:
- `httpx` - Modern HTTP client for API requests
- `python-dotenv` - Environment variable management
- `absl-py` - Google's Python common libraries
- `PyYAML` - YAML configuration file support

Optional dependencies:
- `langfuse` - Observability and tracing (with `--extra tracing`)
- `mem0ai` - Memory system integration (with `--extra memory`)

## Roadmap

Check out our [ROADMAP.md](ROADMAP.md) to see what's planned for future releases, including:

- 🧠 **Multi-LLM Support** - OpenAI, Google AI, and local model integration
- ✅ **Memory & Persistence** - mem0 integration (✅ **COMPLETED**)
- ✅ **3rd Party Integrations** - Observability tools and database services (✅ **COMPLETED**)
- 🛠️ **Advanced Tools** - API discovery, file operations, and code execution
- 🤖 **Agent Intelligence** - Self-reflection, planning, and reasoning capabilities

We welcome feedback and contributions to help shape the project's direction!

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the quality checks:
   ```bash
   uv run ruff check --fix
   uv run ruff format
   uv run mypy .
   uv run pytest
   ```
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

The license is still under development.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for the Claude API
- [Tavily](https://tavily.com/) for web search capabilities
- [mem0](https://mem0.ai/) for AI memory management
- [Langfuse](https://langfuse.com/) for observability and tracing
- The open-source community for inspiration and tools

## Support

- 📚 [Documentation](https://github.com/hanneshapke/agentwerkstatt#readme)
- 🐛 [Bug Reports](https://github.com/hanneshapke/agentwerkstatt/issues)
- 💬 [Discussions](https://github.com/hanneshapke/agentwerkstatt/discussions)
- 🔧 [MEM0 Setup Guide](3rd_party/MEM0_SETUP.md)
- 📊 [Langfuse Integration Guide](3rd_party/LANGFUSE_INTEGRATION.md)

---

**AgentWerkstatt** - Building intelligent agents, one tool at a time. 🚀
