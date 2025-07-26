# AgentWerkstatt 🤖

A minimalistic agentic framework for building AI agents with tool calling capabilities.

## Overview

AgentWerkstatt is a lightweight, extensible framework for creating AI agents powered by Claude (Anthropic). It features a modular architecture with pluggable LLM providers and tools, making it easy to build conversational agents with access to external capabilities like web search.

## Features

- 🧠 **Modular LLM Support** - Built with extensible LLM abstraction (currently supports Claude)
- 🔧 **Tool System** - Pluggable tool architecture with web search capabilities
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
python agent.py
```

Example conversation:
```
🤖 AgentWerkstatt
==================================================

I'm an example AgentWerkstatt assistant with web search capabilities!
Ask me to search the web for information.
Type 'quit', 'exit', or 'clear' to manage the session.

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
from agent import ClaudeAgent

# Initialize the agent
agent = ClaudeAgent()

# Process a request
response = agent.process_request("Search for recent Python releases")
print(response)

# Clear conversation history
agent.llm.clear_history()
```

## Architecture

### Core Components

```
AgentWerkstatt/
├── agent.py           # Main agent implementation
├── llms/              # LLM provider modules
│   ├── base.py        # Base LLM abstraction
│   ├── claude.py      # Claude implementation
│   └── __init__.py
├── tools/             # Tool modules
│   ├── base.py        # Base tool abstraction
│   ├── websearch.py   # Tavily web search tool
│   └── __init__.py
└── pyproject.toml     # Project configuration
```

### LLM Providers

The framework uses a base `BaseLLM` class that can be extended for different providers:

- **Claude (Anthropic)** - Full support with tool calling
- **Future providers** - Easy to add by extending `BaseLLM`

### Tools

Tools are modular components that extend agent capabilities:

- **Web Search** - Tavily API integration for real-time information retrieval
- **Extensible** - Add new tools by implementing `BaseTool`

### Agent System

The `ClaudeAgent` class orchestrates:
- LLM interactions
- Tool execution
- Conversation management
- Response generation

## Development

### Adding a New LLM Provider

1. Create a new file in `llms/` (e.g., `openai.py`)
2. Implement the `BaseLLM` interface:

```python
from .base import BaseLLM

class OpenAILLM(BaseLLM):
    def __init__(self, model_name: str, tools: Dict):
        super().__init__(model_name, tools)
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Set other provider-specific configurations

    def make_api_request(self, messages: List[Dict]) -> Dict:
        # Implement API request logic
        pass

    def process_request(self, messages: List[Dict]) -> str:
        # Implement request processing
        pass
```

3. Update `llms/__init__.py` to export the new provider

### Adding a New Tool

1. Create a new file in `tools/` (e.g., `weather.py`)
2. Implement the `BaseTool` interface:

```python
from .base import BaseTool

class WeatherTool(BaseTool):
    def _get_name(self) -> str:
        return "weather_tool"

    def _get_description(self) -> str:
        return "Get weather information for a location"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
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

    def execute(self, **kwargs) -> Dict[str, Any]:
        # Implement tool logic
        pass
```

3. Update the agent to include your new tool:

```python
self.tools = {
    "websearch_tool": TavilySearchTool(),
    "weather_tool": WeatherTool()
}
```

### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Run tests
pytest

# Run linting
black .
flake8 .
mypy .
```

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - Required for Claude API access
- `TAVILY_API_KEY` - Optional, for web search functionality

### Model Configuration

Default model: `claude-sonnet-4-20250514`

To use a different model:

```python
agent = ClaudeAgent(model="claude-3-5-sonnet-20241022")
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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
