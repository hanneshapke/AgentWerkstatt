# Development Guide

This guide covers everything you need to know about developing with and contributing to AgentWerkstatt.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (for testing with 3rd party services)

### Initial Setup

```bash
# Clone and setup
git clone https://github.com/hanneshapke/agentwerkstatt.git
cd agentwerkstatt
uv sync --dev
```

### Development Dependencies

The development environment includes additional tools:

- **Ruff** - Fast Python linter and formatter (replaces black, flake8, isort)
- **MyPy** - Static type checking
- **Pytest** - Testing framework
- **Pre-commit** - Git hooks for code quality

### Code Quality Tools

```bash
# Code formatting and linting
uv run ruff check --fix
uv run ruff format

# Type checking
uv run mypy .

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/agentwerkstatt --cov-report=html --cov-report=term

# Quick coverage check (uses custom script)
python scripts/check_coverage.py
```

## Adding a New LLM Provider

The framework is designed to be extensible with new LLM providers. Here's how to add one:

### 1. Create the Provider Module

Create a new file in `llms/` (e.g., `openai.py`):

```python
from .base import BaseLLM
import os
import httpx
from typing import List, Dict, Tuple, Any

class OpenAILLM(BaseLLM):
    def __init__(self, model_name: str, tools: list, persona: str = ""):
    super().__init__(model_name, tools, persona)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def make_api_request(self, messages: List[Dict]) -> Dict:
        """Make API request to OpenAI"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "tools": [tool.get_schema() for tool in self.tools] if self.tools else None,
            "tool_choice": "auto" if self.tools else None
        }

        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    def process_request(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Process request and return messages and tool calls"""
        try:
            response = self.make_api_request(messages)
            message = response["choices"][0]["message"]

            # Extract tool calls if present
            tool_calls = []
            if message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    tool_calls.append({
                        "id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "arguments": tool_call["function"]["arguments"]
                    })

            # Add assistant message to conversation
            assistant_message = {
                "role": "assistant",
                "content": message.get("content", "")
            }
            if message.get("tool_calls"):
                assistant_message["tool_calls"] = message["tool_calls"]

            return [assistant_message], tool_calls

        except Exception as e:
            error_message = {
                "role": "assistant",
                "content": f"I encountered an error: {str(e)}"
            }
            return [error_message], []
```

### 2. Update the LLM Registry

Update `llms/__init__.py` to include your new provider:

```python
from .base import BaseLLM
from .claude import ClaudeLLM
from .openai import OpenAILLM  # Add your new provider

__all__ = ["BaseLLM", "ClaudeLLM", "OpenAILLM"]
```

### 3. Update Configuration

Extend the configuration system to support your new provider:

```python
# In config.py or wherever configuration is handled
def create_llm(config: AgentConfig, tools: List[BaseTool]) -> BaseLLM:
    if config.model.startswith("claude"):
        from .llms import ClaudeLLM
        return ClaudeLLM(config.model, tools, config.persona)
    elif config.model.startswith("gpt"):
        from .llms import OpenAILLM
        return OpenAILLM(config.model, tools, config.persona)
    else:
        raise ValueError(f"Unsupported model: {config.model}")
```

## Adding a New Tool

Tools extend agent capabilities and are automatically discovered by the framework.

### 1. Create the Tool Module

Create a new file in `tools/` (e.g., `weather.py`):

```python
from .base import BaseTool
from typing import Any, Dict
import httpx
import os

class WeatherTool(BaseTool):
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY environment variable is required")

    def _get_name(self) -> str:
        return "get_weather"

    def _get_description(self) -> str:
        return "Get current weather information for a specific location"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'London, UK' or 'New York, NY')"
                    },
                    "units": {
                        "type": "string",
                        "description": "Temperature units",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the weather tool"""
        location = kwargs.get("location")
        units = kwargs.get("units", "celsius")

        if not location:
            return {
                "error": "Location is required",
                "success": False
            }

        try:
            # Example using a weather API
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.weatherapi.com/v1/current.json",
                    params={
                        "key": self.api_key,
                        "q": location,
                        "units": "metric" if units == "celsius" else "imperial"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "location": data["location"]["name"],
                    "country": data["location"]["country"],
                    "temperature": data["current"]["temp_c" if units == "celsius" else "temp_f"],
                    "condition": data["current"]["condition"]["text"],
                    "humidity": data["current"]["humidity"],
                    "wind_speed": data["current"]["wind_kph"],
                    "units": units
                }

        except httpx.RequestError as e:
            return {
                "error": f"Failed to fetch weather data: {str(e)}",
                "success": False
            }
        except Exception as e:
            return {
                "error": f"Weather tool error: {str(e)}",
                "success": False
            }
```

### 2. Tool Discovery

The tool will be automatically discovered by the `ToolRegistry` - no manual registration needed! The discovery system:

1. Scans the tools directory for Python files
2. Imports modules and finds classes that inherit from `BaseTool`
3. Instantiates tools and registers them automatically
4. Provides tools to the LLM for function calling

### 3. Tool Testing

Create tests for your tool in `tests/test_tools.py`:

```python
import pytest
from tools.weather import WeatherTool

def test_weather_tool_schema():
    tool = WeatherTool()
    schema = tool.get_schema()

    assert schema["name"] == "get_weather"
    assert "location" in schema["input_schema"]["properties"]
    assert "location" in schema["input_schema"]["required"]

@pytest.mark.integration
def test_weather_tool_execution():
    tool = WeatherTool()
    result = tool.execute(location="London, UK")

    assert result["success"] is True
    assert "temperature" in result
    assert "condition" in result
```

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration and fixtures
├── test_agent.py        # Agent functionality tests
├── test_llms.py         # LLM provider tests
└── test_tools.py        # Tool tests
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_tools.py

# Run with coverage
uv run pytest --cov=src/agentwerkstatt --cov-report=html

# Run integration tests (requires API keys)
uv run pytest -m integration

# Run only unit tests
uv run pytest -m "not integration"
```

### Test Coverage

The project maintains high test coverage with automatic reporting:

- **Target Coverage**: 90% minimum
- **Current Coverage**: [![Coverage](https://codecov.io/gh/hanneshapke/AgentWerkstatt/branch/main/graph/badge.svg)](https://codecov.io/gh/hanneshapke/AgentWerkstatt)
- **Coverage Reports**: Automatically generated on every CI run

#### Local Coverage Checking

```bash
# Quick coverage check with status
python scripts/check_coverage.py

# Detailed coverage report
uv run pytest --cov=src/agentwerkstatt --cov-report=html
# Open htmlcov/index.html in browser for detailed view

# Coverage with missing lines
uv run pytest --cov=src/agentwerkstatt --cov-report=term-missing
```

#### Coverage Integration

- **Codecov**: Automatic coverage reporting on GitHub
- **CI/CD**: Coverage runs on all pull requests
- **Badge**: Dynamic coverage badge in README.md
- **Config**: See `.codecov.yml` for coverage settings

The coverage badge in the README automatically updates based on the latest CI run and links to detailed coverage reports on Codecov.

### Test Categories

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (require API keys/services)
- `@pytest.mark.slow` - Slow tests (may take longer to run)

### Mocking

Use the mock LLM for testing:

```python
from llms.mock import MockLLM

def test_agent_with_mock_llm():
    tools = []
    llm = MockLLM("mock-model", tools, "Test objective")

    # Test agent functionality without API calls
    response = llm.process_request([{"role": "user", "content": "Hello"}])
    assert response is not None
```

## Contributing

### Contribution Workflow

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run quality checks:**
   ```bash
   uv run ruff check --fix
   uv run ruff format
   uv run mypy .
   uv run pytest
   ```
5. **Commit your changes:**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to the branch:**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Code Standards

- **PEP 8** compliance (enforced by Ruff)
- **Type hints** for all public functions
- **Docstrings** for all public classes and methods
- **Tests** for new functionality
- **Clear commit messages**

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
uv run pre-commit install
```

This will run quality checks automatically before each commit.

### Documentation

When adding new features:

- Update relevant documentation in `docs/`
- Add docstrings to new classes and methods
- Include examples in docstrings
- Update the changelog

### Pull Request Guidelines

- **Clear description** of changes and motivation
- **Tests** for new functionality
- **Documentation** updates when applicable
- **Breaking changes** clearly noted
- **Backwards compatibility** maintained when possible

## Debugging

### Logging

Enable verbose logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = AgentConfig(verbose=True)
agent = Agent(config)
```

### Common Issues

1. **API Rate Limits**: Implement retry logic with exponential backoff
2. **Tool Execution Errors**: Add proper error handling and validation
3. **Memory Issues**: Check service connectivity and configuration
4. **Performance**: Profile tool execution and API calls

### Development Tools

- **IPython/Jupyter** - Interactive development and testing
- **Debugger** - Use `pdb` or IDE debugger for step-through debugging
- **Profiling** - Use `cProfile` for performance analysis
- **Monitoring** - Enable Langfuse for production debugging

## Architecture Decisions

### Design Principles

1. **Simplicity** - Keep the codebase minimal and understandable
2. **Modularity** - Clear separation of concerns
3. **Extensibility** - Easy to add new providers and tools
4. **Testability** - Comprehensive test coverage
5. **Documentation** - Well-documented code and APIs

### Technology Choices

- **httpx** - Modern async-capable HTTP client
- **Pydantic** - Data validation and settings management
- **pytest** - Testing framework
- **Ruff** - Fast linting and formatting
- **Docker** - Service orchestration and deployment

## Release Process

### Versioning

AgentWerkstatt follows [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking changes
- **MINOR** - New features (backwards compatible)
- **PATCH** - Bug fixes (backwards compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Update documentation
5. Create release tag
6. Publish to PyPI (when ready)

For detailed contributing guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).
