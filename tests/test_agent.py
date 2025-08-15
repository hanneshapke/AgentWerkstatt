"""
Unit tests for the Agent class
"""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from agentwerkstatt.config import AgentConfig
from agentwerkstatt.llms.mock import MockLLM
from agentwerkstatt.main import Agent
from agentwerkstatt.services.tool_executor import ToolExecutor


class MockMemoryService:
    """Mock memory service for testing"""

    def __init__(self, enabled: bool = True):
        self._enabled = enabled

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def retrieve_memories(self, user_input: str, user_id: str) -> str:
        if user_input == "test with memory":
            return "\nRelevant memories:\n- Previous test conversation\n"
        return ""

    def store_conversation(self, user_input: str, assistant_response: str, user_id: str) -> None:
        pass


class MockObservabilityService:
    """Mock observability service for testing"""

    def __init__(self, enabled: bool = True):
        """Mock observability service"""
        self._enabled = enabled
        self.observations = []
        self.flushed = False
        self.tool_executions = []
        self.observed_requests = []

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def observe_request(self, input_data: str, metadata: dict[str, Any]) -> None:
        """Mock observe request"""
        self.observed_requests.append((input_data, metadata))

    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Mock observe tool execution"""
        self.tool_executions.append({"tool_name": tool_name, "tool_input": tool_input})
        return f"mock_tool_span_{tool_name}"

    def update_tool_observation(self, tool_observation: Any, output: Any) -> None:
        """Mock update tool observation"""
        pass

    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] = None
    ) -> Any:
        """Mock observe LLM call"""
        return f"mock_llm_span_{model_name}"

    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] = None
    ) -> None:
        """Mock update LLM observation"""
        pass

    def update_observation(self, output: Any) -> None:
        """Mock update observation"""
        self.observations.append(output)

    def flush_traces(self) -> None:
        """Mock flush traces"""
        self.flushed = True

    def get_observe_decorator(self, name: str):
        """Mock get observe decorator"""

        def decorator(func):
            return func

        return decorator


class MockToolExecutor:
    """Mock tool executor for testing"""

    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        return {"result": f"Executed {tool_name} with {tool_input}"}

    def execute_tool_calls(self, assistant_message: list) -> tuple[list, list]:
        # Mock no tool calls scenario
        final_response_parts = []
        for block in assistant_message:
            if block.get("type") == "text":
                final_response_parts.append(block["text"])
        return [], final_response_parts


class MockConversationHandler:
    """Mock conversation handler for testing"""

    def __init__(self):
        self._conversation_length = 0

    def process_message(self, user_input: str, enhanced_input: str) -> str:
        self._conversation_length += 2  # User + assistant message
        return f"Mock response to: {user_input}"

    def clear_history(self) -> None:
        self._conversation_length = 0

    @property
    def conversation_length(self) -> int:
        return self._conversation_length

    def enhance_input_with_memory(self, user_input: str) -> str:
        if user_input == "test with memory":
            return (
                "\nRelevant memories:\n- Previous test conversation\n\nUser query: test with memory"
            )
        return user_input


@pytest.fixture
def temp_tools_dir():
    """Create a temporary tools directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        tools_dir = Path(temp_dir)
        (tools_dir / "__init__.py").touch()
        yield str(tools_dir)


@pytest.fixture
def mock_config(temp_tools_dir):
    """Create a mock configuration for testing"""
    return AgentConfig(
        model="claude-3-sonnet-20240229",
        tools_dir=temp_tools_dir,
        verbose=False,
        personas={"default": "Test agent"},
        default_persona="default",
        langfuse_enabled=False,
        memory_enabled=False,
    )


@pytest.fixture
def mock_services():
    """Create mock services for testing"""
    return {
        "llm": MockLLM(),
        "memory_service": MockMemoryService(),
        "observability_service": MockObservabilityService(),
        "tool_executor": MockToolExecutor(),
        "conversation_handler": MockConversationHandler(),
    }


def test_agent_initialization_with_mocks(mock_config):
    """Test that agent can be initialized with mock dependencies"""
    llm = MockLLM()
    memory_service = MockMemoryService()
    observability_service = MockObservabilityService()
    tool_executor = MockToolExecutor()
    conversation_handler = MockConversationHandler()

    agent = Agent(
        config=mock_config,
        llm=llm,
        memory_service=memory_service,
        observability_service=observability_service,
        tool_executor=tool_executor,
        conversation_handler=conversation_handler,
    )

    assert agent.memory_service == memory_service
    assert agent.observability_service == observability_service
    assert agent.tool_executor == tool_executor
    assert agent.conversation_handler == conversation_handler


def test_process_request_with_mocks(mock_config, mock_services):
    """Test processing a request with mock services"""
    agent = Agent(config=mock_config, **mock_services)

    response = agent.process_request("Hello, how are you?")

    assert response == "Mock response to: Hello, how are you?"
    assert len(mock_services["observability_service"].observed_requests) == 1
    assert mock_services["observability_service"].observed_requests[0][0] == "Hello, how are you?"


def test_memory_enhancement_in_process_request(mock_config):
    """Test that memory enhancement works correctly"""
    llm = MockLLM()
    memory_service = MockMemoryService()
    observability_service = MockObservabilityService()
    tool_executor = MockToolExecutor()
    conversation_handler = MockConversationHandler()

    agent = Agent(
        config=mock_config,
        llm=llm,
        memory_service=memory_service,
        observability_service=observability_service,
        tool_executor=tool_executor,
        conversation_handler=conversation_handler,
    )

    response = agent.process_request("test with memory")

    # The conversation handler should receive the enhanced input
    assert response == "Mock response to: test with memory"


def test_observability_metadata(mock_config, mock_services):
    """Test that observability receives correct metadata"""
    agent = Agent(config=mock_config, **mock_services)

    agent.process_request("test message")

    observed = mock_services["observability_service"].observed_requests[0]
    metadata = observed[1]

    assert metadata["model"] == mock_services["llm"].model_name
    assert metadata["project"] == mock_config.langfuse_project_name
    assert metadata["memory_enabled"] == mock_services["memory_service"].is_enabled


def test_agent_with_disabled_services(mock_config):
    """Test agent behavior when services are disabled"""
    llm = MockLLM()
    memory_service = MockMemoryService(enabled=False)
    observability_service = MockObservabilityService(enabled=False)

    agent = Agent(
        config=mock_config,
        llm=llm,
        memory_service=memory_service,
        observability_service=observability_service,
        tool_executor=MockToolExecutor(),
        conversation_handler=MockConversationHandler(),
    )

    assert not agent.memory_service.is_enabled
    assert not agent.observability_service.is_enabled


def test_conversation_length_tracking(mock_config, mock_services):
    """Test that conversation length is tracked correctly"""
    agent = Agent(config=mock_config, **mock_services)

    # Initial state
    assert agent.conversation_handler.conversation_length == 0

    # Process a message
    agent.process_request("First message")
    assert agent.conversation_handler.conversation_length == 2

    # Process another message
    agent.process_request("Second message")
    assert agent.conversation_handler.conversation_length == 4

    # Clear history
    agent.conversation_handler.clear_history()
    assert agent.conversation_handler.conversation_length == 0


# Integration test example
def test_tool_execution_integration():
    """Test that tool execution integrates properly with observability"""
    # Mock a tool
    mock_tool = Mock()
    mock_tool.execute.return_value = {"result": "success"}

    # Mock tool registry
    mock_tool_registry = Mock()
    mock_tool_registry.get_tool_by_name.return_value = mock_tool

    # Mock observability service
    observability_service = MockObservabilityService()

    # Create tool executor
    tool_executor = ToolExecutor(mock_tool_registry, observability_service)

    # Simulate an assistant message with a tool call
    assistant_message = [
        {
            "type": "tool_use",
            "id": "tool_123",
            "name": "test_tool",
            "input": {"param": "value"},
        }
    ]

    results, _ = tool_executor.execute_tool_calls(assistant_message)
    result = results[0] if results else {}

    assert "success" in result.get("content", "")
    # Verify tool execution was observed
    assert len(observability_service.tool_executions) == 1
    tool_execution = observability_service.tool_executions[0]
    assert tool_execution["tool_name"] == "test_tool"
    assert tool_execution["tool_input"] == {"param": "value"}
