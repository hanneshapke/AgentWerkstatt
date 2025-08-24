from functools import wraps
import logging
import os
from typing import Any
from collections.abc import Callable
from abc import ABC, abstractmethod

from ..config import AgentConfig

# Langfuse imports
try:
    from langfuse import Langfuse, get_client, observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

    # Create dummy decorator if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator if args else decorator


def langfuse_enabled_check(f: Callable) -> Callable:
    """Decorator to check if Langfuse is enabled before executing a method."""

    @wraps(f)
    def decorated(self: "LangfuseService", *args, **kwargs):
        if not self.is_enabled:
            return None
        return f(self, *args, **kwargs)

    return decorated


class ObservabilityServiceProtocol(ABC):
    """Defines the interface for an observability and tracing service."""

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Returns True if the observability service is active, False otherwise."""
        raise NotImplementedError

    @abstractmethod
    def observe_request(self, input_data: str, metadata: dict[str, Any]):
        """Starts observing a top-level request."""
        raise NotImplementedError

    @abstractmethod
    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Starts observing a tool execution and returns a span/trace object."""
        raise NotImplementedError

    @abstractmethod
    def update_tool_observation(self, tool_observation: Any, output: Any):
        """Updates the tool observation with the execution's output."""
        raise NotImplementedError

    @abstractmethod
    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] | None = None
    ) -> Any:
        """Starts observing an LLM call and returns a span/generation object."""
        raise NotImplementedError

    @abstractmethod
    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] | None = None
    ):
        """Updates the LLM observation with the model's output and token usage."""
        raise NotImplementedError

    @abstractmethod
    def update_observation(self, output: Any):
        """Updates the current top-level observation with the final output."""
        raise NotImplementedError

    @abstractmethod
    def flush_traces(self):
        """Ensures all pending traces are sent to the observability backend."""
        raise NotImplementedError


class LangfuseService(ObservabilityServiceProtocol):
    """Service for handling Langfuse observability operations"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._client: Any | None = None
        self._enabled = False
        self._current_span: Any | None = None
        self._initialize()

    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse service is enabled"""
        return self._enabled

    def _initialize(self) -> None:
        """Initialize Langfuse service"""
        try:
            if not self._check_availability():
                return

            if not self._validate_configuration():
                return

            self._setup_client()
            logging.info("Langfuse service initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize Langfuse: {e}")
            self._enabled = False

    def _check_availability(self) -> bool:
        """Check if Langfuse is available and enabled"""
        if not LANGFUSE_AVAILABLE:
            if self.config.langfuse_enabled:
                logging.warning(
                    "Langfuse is enabled in config but not installed. Install with: pip install langfuse"
                )
            return False

        if not self.config.langfuse_enabled:
            logging.debug("Langfuse tracing is disabled in configuration")
            return False

        return True

    def _validate_configuration(self) -> bool:
        """Validate required environment variables"""
        required_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            logging.warning(f"Langfuse missing environment variables: {missing_vars}")
            return False

        return True

    def _setup_client(self) -> None:
        """Setup and test Langfuse client"""
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        # Initialize the singleton client
        Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=host,
        )

        # Get client instance and test connection
        self._client = get_client()

        if not self._client.auth_check():
            raise Exception(f"Authentication failed for host: {host}")

        self._enabled = True

    @langfuse_enabled_check
    def observe_request(self, input_data: str, metadata: dict[str, Any]) -> None:
        """Start observing a request by creating a new trace and span"""
        try:
            assert self._client is not None  # Type assertion after availability check
            self._current_span = self._client.start_span(
                name="Agent Request", input=input_data, metadata=metadata
            )

            # Update trace with session metadata
            self._current_span.update_trace(
                name="Agent Processing",
                session_id=metadata.get("session_id"),
                user_id=metadata.get("user_id"),
                tags=["agent", "request"],
            )

            logging.debug(f"Started observation for request (trace: {self._current_span.trace_id})")

        except Exception as e:
            logging.error(f"Failed to observe request: {e}")

    @langfuse_enabled_check
    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> Any | None:
        """Create a generation for tool execution that can be updated later"""
        if not self._current_span:
            return None

        try:
            tool_generation = self._current_span.start_generation(
                name=f"Tool: {tool_name}",
                input=tool_input,
                metadata={"tool_name": tool_name, "type": "tool_execution"},
            )

            logging.debug(f"Started tool observation: {tool_name}")
            return tool_generation

        except Exception as e:
            logging.error(f"Failed to observe tool execution: {e}")
            return None

    @langfuse_enabled_check
    def update_tool_observation(self, tool_generation: Any, output: Any) -> None:
        """Update tool observation with results"""
        if not tool_generation:
            return

        try:
            tool_generation.update(output=output)
            tool_generation.end()
            logging.debug("Tool observation updated successfully")

        except Exception as e:
            logging.error(f"Failed to update tool observation: {e}")

    @langfuse_enabled_check
    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] | None = None
    ) -> Any | None:
        """Create a generation for LLM API calls"""
        if not self._current_span:
            return None

        try:
            llm_generation = self._current_span.start_generation(
                name=f"LLM Call: {model_name}",
                input=messages,
                model=model_name,
                metadata={"type": "llm_call", **(metadata or {})},
            )

            logging.debug(f"Started LLM observation: {model_name}")
            return llm_generation

        except Exception as e:
            logging.error(f"Failed to observe LLM call: {e}")
            return None

    @langfuse_enabled_check
    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] | None = None
    ) -> None:
        """Update LLM observation with output and usage data"""
        if not llm_generation:
            return

        try:
            update_data = {"output": output}
            if usage:
                update_data["usage_details"] = usage

            llm_generation.update(**update_data)
            llm_generation.end()
            logging.debug("LLM observation updated successfully")

        except Exception as e:
            logging.error(f"Failed to update LLM observation: {e}")

    @langfuse_enabled_check
    def update_observation(self, output: Any) -> None:
        """Update current observation with final output and end the span"""
        if not self._current_span:
            return

        try:
            # Update span and trace with final output
            self._current_span.update(output=output)
            self._current_span.update_trace(output=output)
            self._current_span.end()

            # Clear current span
            self._current_span = None
            logging.debug("Request observation completed")

        except Exception as e:
            logging.error(f"Failed to update observation: {e}")

    @langfuse_enabled_check
    def flush_traces(self) -> None:
        """Flush any pending Langfuse traces"""
        try:
            assert self._client is not None  # Type assertion after availability check
            self._client.flush()
            logging.debug("Langfuse traces flushed")
        except Exception as e:
            logging.error(f"Failed to flush traces: {e}")

    def get_observe_decorator(self, name: str):
        """Get the observe decorator for function decoration"""
        if self._enabled:
            return observe(name=name)

        # Return no-op decorator
        def decorator(func):
            return func

        return decorator

    def _is_available(self) -> bool:
        """Check if service is enabled and client is available"""
        return self._enabled and self._client is not None


class NoOpObservabilityService(ObservabilityServiceProtocol):
    """No-operation observability service for when Langfuse is disabled"""

    @property
    def is_enabled(self) -> bool:
        return False

    def observe_request(self, input_data: str, metadata: dict[str, Any]) -> None:
        pass

    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        return None

    def update_tool_observation(self, tool_observation: Any, output: Any) -> None:
        pass

    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] | None = None
    ) -> None:
        return None

    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] | None = None
    ) -> None:
        pass

    def update_observation(self, output: Any) -> None:
        pass

    def flush_traces(self) -> None:
        pass

    def get_observe_decorator(self, name: str):
        def decorator(func):
            return func

        return decorator
