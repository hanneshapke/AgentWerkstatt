# Configuration

This document covers all configuration options for AgentWerkstatt, including environment variables, configuration files, and runtime settings.

## Environment Variables

AgentWerkstatt uses environment variables for API keys and sensitive configuration. Create a `.env` file in your project root:

### Core Configuration

- `ANTHROPIC_API_KEY` - **Required** for Claude API access
- `TAVILY_API_KEY` - **Optional**, for web search functionality

### Memory System (mem0)

- `OPENAI_API_KEY` - **Required** for mem0 memory system (LLM and embeddings)

### Observability (Langfuse)

- `LANGFUSE_PUBLIC_KEY` - **Optional**, for Langfuse tracing integration
- `LANGFUSE_SECRET_KEY` - **Optional**, for Langfuse tracing integration
- `LANGFUSE_HOST` - **Optional**, Langfuse host URL (defaults to cloud.langfuse.com)

### Example .env file

```bash
# Core API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Memory System
OPENAI_API_KEY=your_openai_api_key_here

# Observability (Optional)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Configuration File

AgentWerkstatt uses YAML configuration files for non-sensitive settings. The default configuration file is `config.yaml`.

### Default Configuration

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

### Configuration Options

#### LLM Configuration

- `model`: The LLM model to use (currently supports Claude models)
- `agent_objective`: System prompt/objective for the agent

#### Tools Configuration

- `tools_dir`: Directory containing tool modules (relative to project root)

#### Logging Configuration

- `verbose`: Enable detailed logging output

#### Memory Configuration

- `memory.enabled`: Enable/disable mem0 memory integration
- `memory.model_name`: LLM model for memory operations
- `memory.server_url`: mem0 server endpoint URL

#### Langfuse Configuration

- `langfuse.enabled`: Enable/disable Langfuse tracing
- `langfuse.project_name`: Project name in Langfuse

## Memory Configuration

To enable persistent memory with mem0:

1. **Install memory dependencies:**
   ```bash
   uv sync --extra memory
   ```

2. **Start the mem0 service:**
   ```bash
   docker compose -f third_party/docker-compose.yaml up -d mem0
   ```

3. **Set your OpenAI API key** for memory operations in your `.env` file

4. **Enable memory in your configuration:**
   ```yaml
   memory:
     enabled: true
     model_name: "gpt-4o-mini"
     server_url: "http://localhost:8000"
   ```

### Memory Service Components

The memory system uses several components:

- **mem0 Server**: REST API for memory operations
- **PostgreSQL**: Vector database with pgvector extension
- **Neo4j**: Graph database for relationships
- **OpenAI**: Embeddings and LLM for memory processing

## Model Configuration

### Supported Models

Currently supported Claude models:
- `claude-sonnet-4-20250514` (default)
- `claude-haiku-3-20240307`
- `claude-opus-3-20240229`

### Programmatic Model Configuration

```python
from agentwerkstatt import Agent, AgentConfig

# Use a different model
config = AgentConfig(model="claude-haiku-3-20240307")
agent = Agent(config)
```

## Observability with Langfuse

AgentWerkstatt includes optional integration with [Langfuse](https://langfuse.com) for comprehensive observability.

### Features

- **Automatic Tracing**: All agent interactions, LLM calls, and tool executions
- **Performance Monitoring**: Track costs, latency, and token usage
- **Debugging**: Detailed execution flow for troubleshooting
- **Analytics**: Historical data and performance insights

### Setup

1. **Install the tracing dependencies:**
   ```bash
   uv sync --extra tracing
   ```

2. **Set up your Langfuse credentials** in your `.env` file

3. **Enable tracing in your configuration:**
   ```yaml
   langfuse:
     enabled: true
     project_name: "your-project-name"
   ```

**Note**: Langfuse is completely optional. AgentWerkstatt works perfectly without it.

For detailed setup instructions, see [LANGFUSE_INTEGRATION.md](../third_party/LANGFUSE_INTEGRATION.md).

## Runtime Configuration

### Programmatic Configuration

```python
from agentwerkstatt import Agent, AgentConfig

# Load from YAML file
config = AgentConfig.from_yaml("config.yaml")

# Or create programmatically
config = AgentConfig(
    model="claude-sonnet-4-20250514",
    tools_dir="./tools",
    verbose=True,
    agent_objective="You are a helpful assistant with web search capabilities.",
    memory_enabled=True,
    langfuse_enabled=True
)

agent = Agent(config)
```

### Custom Configuration Files

You can use custom configuration files:

```bash
# Use custom configuration
python agent.py --config my_custom_config.yaml
```

Example custom configuration:

```yaml
# my_custom_config.yaml
model: "claude-haiku-3-20240307"
tools_dir: "./custom_tools"
verbose: false

memory:
  enabled: true
  model_name: "gpt-4o"
  server_url: "http://localhost:8000"

langfuse:
  enabled: false

agent_objective: |
  You are a specialized research assistant.
  Focus on providing detailed, accurate information with proper citations.
```

## Configuration Validation

AgentWerkstatt validates configuration on startup:

- **Required fields**: Ensures all required configuration is present
- **API keys**: Validates that required API keys are available
- **File paths**: Checks that specified directories and files exist
- **Service connectivity**: Tests connections to optional services when enabled

### Error Messages

Common configuration errors and solutions:

- **Missing ANTHROPIC_API_KEY**: Add your Anthropic API key to `.env`
- **Invalid tools directory**: Ensure the tools directory exists and is readable
- **mem0 connection failed**: Check that mem0 service is running and accessible
- **Langfuse authentication failed**: Verify your Langfuse credentials

## Advanced Configuration

### Custom Tool Discovery

You can customize tool discovery by modifying the tools directory structure:

```
tools/
├── __init__.py
├── base.py              # Base tool class
├── websearch.py         # Web search tool
├── custom/              # Custom tools subdirectory
│   ├── __init__.py
│   └── my_tool.py
└── external/            # External tools
    ├── __init__.py
    └── api_tool.py
```

### Environment-Specific Configuration

Use different configuration files for different environments:

```bash
# Development
python agent.py --config configs/dev.yaml

# Production
python agent.py --config configs/prod.yaml

# Testing
python agent.py --config configs/test.yaml
```

### Configuration Inheritance

You can extend base configurations:

```yaml
# base.yaml
model: "claude-sonnet-4-20250514"
tools_dir: "./tools"
verbose: true

# production.yaml (extends base.yaml)
extends: "base.yaml"
verbose: false
memory:
  enabled: true
langfuse:
  enabled: true
  project_name: "production-agent"
```

## Troubleshooting

### Common Issues

1. **API Rate Limits**: Configure retry logic and delays
2. **Memory Service Unavailable**: Check Docker services and network connectivity
3. **Tool Loading Errors**: Verify tool module syntax and dependencies
4. **Configuration Parsing Errors**: Validate YAML syntax and structure

### Debug Mode

Enable debug mode for detailed logging:

```yaml
verbose: true
debug: true  # Additional debug information
```

Or programmatically:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = AgentConfig(verbose=True, debug=True)
```
