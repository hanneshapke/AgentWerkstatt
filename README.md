<p align="center">
  <img src="https://github.com/hanneshapke/AgentWerkstatt/blob/main/misc/agent-werkstatt-logo.png?raw=true" alt="AgentWerkstatt Logo" width="400">
</p>

# AgentWerkstatt 🤖

A minimalistic agentic framework for building AI agents with tool calling capabilities.

## Overview

AgentWerkstatt is a lightweight, extensible framework for creating AI agents powered by Claude (Anthropic). It features a modular architecture with pluggable LLM providers and tools, making it easy to build conversational agents with access to external capabilities like web search.

## Features

- 🧠 **Modular LLM Support** - Built with extensible LLM abstraction (currently supports Claude)
- 🔧 **Tool System** - Pluggable tool architecture with automatic tool discovery
- 💬 **Conversation Management** - Built-in conversation history and context management
- 🌐 **Web Search** - Integrated Tavily API for real-time web information retrieval
- 🖥️ **CLI Interface** - Ready-to-use command-line interface
- ⚡ **Lightweight** - Minimal dependencies and clean architecture

## Quick Start

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key for Claude
- (Optional) A Tavily API key for web search

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hanneshapke/agentwerkstatt.git
   cd agentwerkstatt
   ```

2. **Install dependencies:**
   ```bash
   # Using uv
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   # Create a .env file
   echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env
   echo "TAVILY_API_KEY=your_tavily_api_key_here" >> .env  # Optional for web search
   ```

### API Keys Setup

#### Anthropic API Key (Required)
1. Sign up at [console.anthropic.com](https://console.anthropic.com/)
2. Generate an API key
3. Add it to your `.env` file as `ANTHROPIC_API_KEY`

#### Tavily API Key (Optional, for web search)
1. Sign up at [app.tavily.com](https://app.tavily.com/)
2. Get your API key (1,000 free searches/month)
3. Add it to your `.env` file as `TAVILY_API_KEY`

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

### Agent System

The `Agent` class orchestrates:
- LLM interactions
- Tool execution and discovery
- Conversation management
- Response generation

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - Required for Claude API access
- `TAVILY_API_KEY` - Optional, for web search functionality

### Configuration File

Default configuration in `agent_config.yaml`:

```yaml
# LLM Model Configuration
model: "claude-sonnet-4-20250514"

# Tools Configuration
tools_dir: "./tools"

# Logging Configuration
verbose: true

# Agent Objective/System Prompt
agent_objective: |
  You are a helpful assistant with web search capabilities.
  You can search the web for current information and provide accurate, helpful responses.
  Always be conversational and helpful in your responses.
```

### Model Configuration

To use a different model programmatically:

```python
config = AgentConfig(model="claude-3-5-sonnet-20241022")
agent = Agent(config)
```

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
- The open-source community for inspiration and tools

## Support

- 📚 [Documentation](https://github.com/hanneshapke/agentwerkstatt#readme)
- 🐛 [Bug Reports](https://github.com/hanneshapke/agentwerkstatt/issues)
- 💬 [Discussions](https://github.com/hanneshapke/agentwerkstatt/discussions)

---

**AgentWerkstatt** - Building intelligent agents, one tool at a time. 🚀
