<p align="center">
  <img src="https://github.com/hanneshapke/AgentWerkstatt/blob/main/docs/agent-werkstatt-logo.png?raw=true" alt="AgentWerkstatt Logo" width="400">
</p>

<p align="center">
  <a href="https://github.com/hanneshapke/agentwerkstatt/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
  </a>
  <a href="https://github.com/hanneshapke/agentwerkstatt">
    <img src="https://img.shields.io/github/stars/hanneshapke/agentwerkstatt?style=social" alt="GitHub Stars">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+">
  </a>
  <a href="https://github.com/hanneshapke/agentwerkstatt/issues">
    <img src="https://img.shields.io/github/issues/hanneshapke/agentwerkstatt" alt="GitHub Issues">
  </a>
  <a href="https://github.com/hanneshapke/agentwerkstatt/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg" alt="Contributions Welcome">
  </a>
  <a href="https://github.com/hanneshapke/agentwerkstatt/pulls">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
  </a>
</p>

<p align="center">
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff">
  </a>
  <a href="https://docs.astral.sh/uv/">
    <img src="https://img.shields.io/badge/uv-dependency%20manager-blue?logo=uv" alt="uv">
  </a>
</p>

# AgentWerkstatt 🤖

### Agents for Minimalists.

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
docker compose -f third_party/docker-compose.yaml up -d

# Or start specific services
docker compose -f third_party/docker-compose.yaml up -d mem0 neo4j postgres
```

For detailed setup instructions, see:
- [MEM0_SETUP.md](third_party/MEM0_SETUP.md) - Memory system setup
- [LANGFUSE_SETUP.md](third_party/LANGFUSE_SETUP.md) - Observability setup
- [LANGFUSE_INTEGRATION.md](third_party/LANGFUSE_INTEGRATION.md) - Integration guide

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

#### Programmatic Usage

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
    persona="You are a helpful assistant with web search capabilities."
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

## Documentation

For comprehensive documentation, please visit our [documentation directory](docs/):

- 📚 **[Complete Documentation](docs/index.md)** - Main documentation hub
- 🚀 **[Getting Started](docs/getting-started.md)** - Installation and quick start guide
- 🏗️ **[Architecture](docs/architecture.md)** - Framework design and components
- ⚙️ **[Configuration](docs/configuration.md)** - Environment setup and configuration options
- 🛠️ **[Development Guide](docs/development.md)** - Contributing and extending the framework
- 📖 **[API Reference](docs/api-reference.md)** - Detailed API documentation

## Quick Configuration Reference

Basic configuration in `config.yaml`:

```yaml
# LLM Model Configuration
model: "claude-sonnet-4-20250514"

# Tools Configuration
tools_dir: "./tools"

# Logging Configuration
verbose: true

# Agent Objective/System Prompt
persona: |
  You are a helpful assistant with web search capabilities.
  You can search the web for current information and provide accurate, helpful responses.
  Always be conversational and helpful in your responses.
```

**Environment Variables:**
- `ANTHROPIC_API_KEY` - Required for Claude API access
- `TAVILY_API_KEY` - Optional, for web search functionality

For complete configuration options, see the [Configuration Guide](docs/configuration.md).

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

- 📚 [Documentation](docs/index.md)
- 🐛 [Bug Reports](https://github.com/hanneshapke/agentwerkstatt/issues)
- 💬 [Discussions](https://github.com/hanneshapke/agentwerkstatt/discussions)
- 🔧 [MEM0 Setup Guide](third_party/MEM0_SETUP.md)
- 📊 [Langfuse Integration Guide](third_party/LANGFUSE_INTEGRATION.md)

---

**AgentWerkstatt** - Building intelligent agents, one tool at a time. 🚀
