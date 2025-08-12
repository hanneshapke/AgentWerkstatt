# Architecture

This document describes the architecture and core components of AgentWerkstatt.

## Overview

AgentWerkstatt follows a modular architecture with clear separation of concerns, making it easy to extend and customize for different use cases.

## Core Components

```
AgentWerkstatt/
├── agent.py               # Main agent implementation and CLI
├── config.yaml      # Default configuration
├── llms/                  # LLM provider modules
│   ├── base.py           # Base LLM abstraction
│   ├── claude.py         # Claude implementation
│   └── __init__.py
├── tools/                # Tool modules
│   ├── base.py          # Base tool abstraction
│   ├── discovery.py     # Automatic tool discovery
│   ├── websearch.py     # Tavily web search tool
│   └── __init__.py
├── services/             # Core services
│   ├── conversation_handler.py  # Conversation management
│   ├── langfuse_service.py     # Observability service
│   ├── memory_service.py       # Memory management
│   └── tool_executor.py        # Tool execution
├── third_party/         # Third-party service integrations
│   ├── docker-compose.yaml    # Service orchestration
│   ├── Dockerfile.mem0        # Custom mem0 build
│   ├── mem0-config.yaml       # Memory system config
│   ├── MEM0_SETUP.md          # Memory setup guide
│   ├── LANGFUSE_SETUP.md      # Observability setup
│   └── LANGFUSE_INTEGRATION.md # Integration guide
└── pyproject.toml       # Project configuration
```

## LLM Providers

The framework uses a base `BaseLLM` class that can be extended for different providers:

- **Claude (Anthropic)** - Full support with tool calling
- **Future providers** - Easy to add by extending `BaseLLM`

### LLM Abstraction

The `BaseLLM` class provides a common interface for all LLM providers:

```python
class BaseLLM:
    def __init__(self, model_name: str, tools: list, agent_objective: str = ""):
        self.model_name = model_name
        self.tools = tools
        self.agent_objective = agent_objective
        self.conversation_history = []

    def make_api_request(self, messages: list[dict]) -> dict:
        """Make API request to the LLM provider"""
        raise NotImplementedError

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list[dict]]:
        """Process request and return messages and tool calls"""
        raise NotImplementedError
```

## Tools

Tools are modular components that extend agent capabilities:

- **Web Search** - Tavily API integration for real-time information retrieval
- **Automatic Discovery** - Tools are automatically discovered from the tools directory
- **Extensible** - Add new tools by implementing `BaseTool`

### Tool System

The tool system is built around the `BaseTool` abstraction:

```python
class BaseTool:
    def get_name(self) -> str:
        """Return the tool name"""
        return self._get_name()

    def get_description(self) -> str:
        """Return the tool description"""
        return self._get_description()

    def get_schema(self) -> dict[str, Any]:
        """Return the tool schema for LLM"""
        raise NotImplementedError

    def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool with given parameters"""
        raise NotImplementedError
```

### Tool Discovery

Tools are automatically discovered using the `ToolRegistry`:

1. Scans the tools directory for Python files
2. Imports modules and finds classes that inherit from `BaseTool`
3. Instantiates tools and registers them automatically
4. Provides tools to the LLM for function calling

## Services

### Conversation Handler

Manages conversation flow and state:
- Message processing
- History management
- Context preservation
- Response formatting

### Tool Executor

Handles tool execution:
- Tool validation
- Parameter processing
- Execution coordination
- Result formatting

### Memory Service

Optional persistent memory using mem0:
- Long-term context storage
- Semantic search capabilities
- Vector embeddings
- Graph relationships

### Langfuse Service

Optional observability and tracing:
- Request/response logging
- Performance monitoring
- Error tracking
- Analytics

## Memory System

Optional mem0 integration provides:

- **Persistent Context** - Long-term memory across conversations
- **Semantic Search** - Vector-based memory retrieval
- **Graph Relationships** - Knowledge graph storage in Neo4j
- **REST API** - Direct access to memory operations

### Memory Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AgentWerkstatt│    │      mem0       │    │    Neo4j        │
│                 │    │    Server       │    │   Database      │
│   ┌─────────────┤    │                 │    │                 │
│   │ Memory      │────│   REST API      │────│  Graph Storage  │
│   │ Service     │    │                 │    │                 │
│   └─────────────┤    │   Vector Store  │    │   Relationships │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Agent System

The `Agent` class orchestrates:
- LLM interactions
- Tool execution and discovery
- Conversation management
- Response generation
- Memory persistence (when enabled)

### Agent Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │   Agent     │    │    LLM      │    │   Tools     │
│   Input     │───▶│  Process    │───▶│  Generate   │───▶│  Execute    │
│             │    │             │    │  Response   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │ Conversation│    │   Memory    │    │   Result    │
                   │  History    │    │  Service    │    │ Processing  │
                   └─────────────┘    └─────────────┘    └─────────────┘
```

## Configuration System

Configuration is managed through:

1. **YAML Configuration Files** - Main configuration settings
2. **Environment Variables** - API keys and sensitive data
3. **Runtime Configuration** - Programmatic configuration options

## Error Handling

The framework includes comprehensive error handling:

- **API Errors** - Graceful handling of LLM API failures
- **Tool Errors** - Tool execution error recovery
- **Configuration Errors** - Clear validation and messaging
- **Network Errors** - Retry logic and fallback mechanisms

## Extensibility

The architecture is designed for easy extension:

- **New LLM Providers** - Implement `BaseLLM` interface
- **Custom Tools** - Implement `BaseTool` interface
- **Service Integration** - Add new services following existing patterns
- **Configuration Options** - Extend configuration schema

## Performance Considerations

- **Lazy Loading** - Components loaded on demand
- **Connection Pooling** - Efficient HTTP client usage
- **Caching** - Optional caching for repeated operations
- **Async Support** - Ready for async/await patterns (future enhancement)
