# API Reference

This document provides detailed API documentation for AgentWerkstatt's main classes and modules.

## Core Classes

### Agent

The main `Agent` class orchestrates all interactions between LLMs, tools, and services.

```python
class Agent:
    def __init__(self, config: AgentConfig):
        """Initialize an Agent with the given configuration.

        Args:
            config: AgentConfig object containing all settings
        """
```

#### Methods

- **`process_request(user_input: str) -> str`**

  Process a user request and return the agent's response.

  ```python
  agent = Agent(config)
  response = agent.process_request("What's the weather like today?")
  print(response)
  ```

- **`get_conversation_history() -> List[Dict[str, str]]`**

  Get the current conversation history.

  ```python
  history = agent.get_conversation_history()
  for message in history:
      print(f"{message['role']}: {message['content']}")
  ```

- **`clear_conversation() -> None`**

  Clear the conversation history.

  ```python
  agent.clear_conversation()
  ```

### AgentConfig

Configuration class for Agent initialization.

```python
class AgentConfig:
    def __init__(
        self,
        model: str = "claude-4-sonnet-20250514",
        tools_dir: str = "./tools",
        verbose: bool = True,
        persona: str = "",
        memory_enabled: bool = False,
        langfuse_enabled: bool = False
    ):
        """Initialize agent configuration.

        Args:
            model: LLM model identifier
            tools_dir: Directory containing tool modules
            verbose: Enable verbose logging
            persona: System prompt for the agent
            memory_enabled: Enable mem0 memory integration
            langfuse_enabled: Enable Langfuse tracing
        """
```

#### Class Methods

- **`from_yaml(file_path: str) -> AgentConfig`**

  Load configuration from a YAML file.

  ```python
  config = AgentConfig.from_yaml("config.yaml")
  agent = Agent(config)
  ```

#### Properties

- `model: str` - The LLM model to use
- `tools_dir: str` - Directory containing tools
- `verbose: bool` - Verbose logging flag
- `persona: str` - System prompt/persona
- `memory_enabled: bool` - Memory system flag
- `langfuse_enabled: bool` - Tracing flag

## LLM Module

### BaseLLM

Abstract base class for LLM providers.

```python
class BaseLLM:
    def __init__(self, model_name: str, tools: List[BaseTool], persona: str = ""):
        """Initialize the LLM with model, tools, and objective.

        Args:
            model_name: Name/identifier of the model
            tools: List of available tools
            persona: System prompt or persona
        """
```

#### Abstract Methods

- **`make_api_request(messages: List[Dict]) -> Dict`**

  Make an API request to the LLM provider.

- **`process_request(messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]`**

  Process a request and return messages and tool calls.

#### Methods

- **`add_message(role: str, content: str) -> None`**

  Add a message to the conversation history.

- **`clear_history() -> None`**

  Clear the conversation history.

- **`get_history() -> List[Dict[str, str]]`**

  Get the current conversation history.

### ClaudeLLM

Claude (Anthropic) implementation of BaseLLM.

```python
class ClaudeLLM(BaseLLM):
    def __init__(self, model_name: str, tools: List[BaseTool], persona: str = ""):
        """Initialize Claude LLM.

        Requires ANTHROPIC_API_KEY environment variable.
        """
```

#### Supported Models

- `claude-4-sonnet-20250514` (default)
- `claude-haiku-3-20240307`
- `claude-opus-3-20240229`

## Tools Module

### BaseTool

Abstract base class for all tools.

```python
class BaseTool:
    def get_name(self) -> str:
        """Return the tool name."""

    def get_description(self) -> str:
        """Return the tool description."""

    def get_schema(self) -> Dict[str, Any]:
        """Return the tool schema for LLM function calling."""

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
```

#### Abstract Methods

- **`_get_name() -> str`** - Implementation-specific name
- **`_get_description() -> str`** - Implementation-specific description
- **`get_schema() -> Dict[str, Any]`** - Tool schema for LLM
- **`execute(**kwargs) -> Dict[str, Any]`** - Tool execution logic

### WebSearchTool

Web search tool using Tavily API.

```python
class WebSearchTool(BaseTool):
    def __init__(self):
        """Initialize web search tool.

        Requires TAVILY_API_KEY environment variable.
        """
```

#### Methods

- **`execute(query: str, **kwargs) -> Dict[str, Any]`**

  Perform a web search.

  ```python
  tool = WebSearchTool()
  result = tool.execute(query="latest AI developments")
  print(result["results"])
  ```

### ToolRegistry

Automatic tool discovery and registration system.

```python
class ToolRegistry:
    @staticmethod
    def discover_tools(tools_dir: str) -> List[BaseTool]:
        """Discover and instantiate tools from directory.

        Args:
            tools_dir: Directory to scan for tool modules

        Returns:
            List of instantiated tool objects
        """
```

## Services Module

### ConversationHandler

Manages conversation flow and state.

```python
class ConversationHandler:
    def __init__(self, llm: BaseLLM, tools: List[BaseTool]):
        """Initialize conversation handler.

        Args:
            llm: LLM instance for processing
            tools: Available tools for execution
        """
```

#### Methods

- **`process_message(message: str) -> str`**

  Process a user message and return response.

- **`get_conversation_state() -> Dict[str, Any]`**

  Get current conversation state and metadata.

### ToolExecutor

Handles tool execution and result processing.

```python
class ToolExecutor:
    def __init__(self, tools: List[BaseTool]):
        """Initialize tool executor with available tools.

        Args:
            tools: List of available tool instances
        """
```

#### Methods

- **`execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]`**

  Execute a specific tool with given parameters.

- **`get_available_tools() -> List[str]`**

  Get list of available tool names.

### MemoryService

Optional mem0 integration for persistent memory.

```python
class MemoryService:
    def __init__(self, config: Dict[str, Any]):
        """Initialize memory service.

        Args:
            config: Memory configuration including server URL and model
        """
```

#### Methods

- **`store_memory(text: str, metadata: Dict[str, Any] = None) -> str`**

  Store information in memory.

- **`search_memory(query: str, limit: int = 10) -> List[Dict[str, Any]]`**

  Search stored memories.

- **`get_relevant_memories(query: str) -> List[Dict[str, Any]]`**

  Get memories relevant to current query.

### LangfuseService

Optional Langfuse integration for observability.

```python
class LangfuseService:
    def __init__(self, config: Dict[str, Any]):
        """Initialize Langfuse service.

        Args:
            config: Langfuse configuration including project name
        """
```

#### Methods

- **`trace_request(request: str, response: str, metadata: Dict[str, Any] = None) -> None`**

  Trace a request-response pair.

- **`trace_tool_execution(tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any]) -> None`**

  Trace tool execution.

## Configuration Module

### Environment Variables

The framework uses these environment variables:

```python
# Required
ANTHROPIC_API_KEY: str  # Claude API access

# Optional
TAVILY_API_KEY: str     # Web search functionality
OPENAI_API_KEY: str     # mem0 memory system
LANGFUSE_PUBLIC_KEY: str  # Langfuse tracing
LANGFUSE_SECRET_KEY: str  # Langfuse tracing
LANGFUSE_HOST: str      # Langfuse host URL
```

## Error Handling

### AgentWerkstattError

Base exception class for framework errors.

```python
class AgentWerkstattError(Exception):
    """Base exception for AgentWerkstatt errors."""
    pass
```

### Specific Exceptions

- **`LLMError`** - LLM provider errors
- **`ToolError`** - Tool execution errors
- **`ConfigurationError`** - Configuration validation errors
- **`APIKeyError`** - Missing or invalid API keys

## Usage Examples

### Basic Agent Setup

```python
from agentwerkstatt import Agent, AgentConfig

# Load configuration
config = AgentConfig.from_yaml("config.yaml")

# Create agent
agent = Agent(config)

# Process requests
response = agent.process_request("What's the latest news about AI?")
print(response)
```

### Custom Configuration

```python
from agentwerkstatt import Agent, AgentConfig

# Custom configuration
config = AgentConfig(
    model="claude-haiku-3-20240307",
    tools_dir="./custom_tools",
    verbose=True,
    persona="You are a research assistant specializing in scientific papers.",
    memory_enabled=True,
    langfuse_enabled=True
)

agent = Agent(config)
```

### Tool Development

```python
from tools.base import BaseTool
from typing import Any, Dict

class CalculatorTool(BaseTool):
    def _get_name(self) -> str:
        return "calculator"

    def _get_description(self) -> str:
        return "Perform basic mathematical calculations"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        expression = kwargs.get("expression")
        try:
            result = eval(expression)  # Note: Use safe_eval in production
            return {"result": result, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
```

### Memory Integration

```python
from agentwerkstatt import Agent, AgentConfig

# Enable memory
config = AgentConfig(
    memory_enabled=True,
    # ... other config
)

agent = Agent(config)

# Memory will automatically store and retrieve relevant context
response = agent.process_request("Remember that I prefer Python over JavaScript")
# Later...
response = agent.process_request("What programming language do I prefer?")
```

## Type Hints

The framework uses comprehensive type hints for better IDE support and type checking:

```python
from typing import List, Dict, Any, Optional, Tuple, Union

# Example type signatures
def process_request(self, user_input: str) -> str: ...
def get_tools(self) -> List[BaseTool]: ...
def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]: ...
```

Run type checking with:

```bash
uv run mypy .
```
