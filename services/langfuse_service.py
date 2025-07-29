import logging
import os
from typing import Any

from ..config import AgentConfig

# Langfuse imports
try:
    from langfuse import Langfuse, get_client, observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

    # Create dummy decorators if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator if args else decorator


class LangfuseService:
    """Service for handling Langfuse observability operations"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._client = None
        self._enabled = False
        self._current_trace = None
        self._current_span = None
        self._initialize_langfuse()

    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse service is enabled"""
        return self._enabled

    def _initialize_langfuse(self) -> None:
        """Initialize Langfuse if enabled and available"""
        print(f"🔧 Langfuse setup - LANGFUSE_AVAILABLE: {LANGFUSE_AVAILABLE}")
        print(f"🔧 Langfuse setup - config.langfuse_enabled: {self.config.langfuse_enabled}")

        if not LANGFUSE_AVAILABLE:
            if self.config.langfuse_enabled:
                logging.warning(
                    "Langfuse is enabled in config but not installed. Install with: pip install langfuse"
                )
            print("❌ Langfuse not available")
            return

        if not self.config.langfuse_enabled:
            logging.debug("Langfuse tracing is disabled")
            print("❌ Langfuse disabled in config")
            return

        # Check for required environment variables
        required_env_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        print(f"🔧 Checking environment variables: {required_env_vars}")
        print(f"🔧 Missing variables: {missing_vars}")

        if missing_vars:
            logging.warning(
                f"Langfuse is enabled but missing environment variables: {missing_vars}"
            )
            print(f"❌ Missing env vars: {missing_vars}")
            return

        # Initialize Langfuse client with explicit configuration (v3 API)
        try:
            # Get host configuration
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

            # Initialize the singleton client (v3 pattern)
            Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=langfuse_host,
            )

            # Get the client instance to test connection
            self._client = get_client()

            # Test the connection
            print("🔧 Testing authentication...")
            auth_result = self._client.auth_check()
            print(f"🔧 Auth result: {auth_result}")
            if not auth_result:
                logging.error(
                    f"Langfuse authentication failed. Check your credentials and host: {langfuse_host}"
                )
                print("❌ Authentication failed")
                return

            self._enabled = True
            logging.info(f"Langfuse tracing initialized successfully. Host: {langfuse_host}")
            print("✅ Langfuse setup completed successfully!")

        except Exception as e:
            logging.error(f"Failed to initialize Langfuse: {e}")
            print(f"❌ Langfuse setup failed: {e}")
            self._enabled = False

    def observe_request(self, input_data: str, metadata: dict[str, Any]) -> None:
        """Start observing a request by creating a new trace and span"""
        if not self._enabled or not self._client:
            return

        try:
            logging.debug("Creating Langfuse trace for agent request")

            # Extract session_id from metadata
            session_id = metadata.get("session_id")

            # Create a new span for this request using the correct v3.2.1 API
            self._current_span = self._client.start_span(
                name="Agent Request", input=input_data, metadata=metadata
            )

            # Update the trace with metadata using the span
            self._current_span.update_trace(
                name="Agent Processing",
                session_id=session_id,  # Now properly using the session_id
                user_id=metadata.get("user_id"),
                tags=["agent", "request"],
            )

            # Store reference to the trace ID for child spans
            self._current_trace = self._current_span  # The span provides access to trace operations

            if session_id:
                logging.debug(
                    f"Created span {self._current_span.id} with trace {self._current_span.trace_id} in session {session_id}"
                )
            else:
                logging.debug(
                    f"Created span {self._current_span.id} with trace {self._current_span.trace_id}"
                )

        except Exception as e:
            logging.error(f"Failed to observe request: {e}")

    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Observe tool execution by creating a child span"""
        if not self._enabled or not self._client or not self._current_span:
            return

        try:
            # Create a child span for tool execution using the correct v3.2.1 API
            with self._current_span.start_as_current_span(
                name=f"Tool: {tool_name}",
                input=tool_input,
                metadata={"tool_name": tool_name, "type": "tool_execution"},
            ) as tool_span:
                # The span will automatically end when exiting the context
                tool_span.update(output={"status": "executed"})

            logging.debug(f"Created tool span for {tool_name}")

        except Exception as e:
            logging.error(f"Failed to observe tool execution: {e}")

    def update_observation(self, output: Any) -> None:
        """Update current observation with output and end the span"""
        if not self._enabled or not self._client or not self._current_span:
            return

        try:
            # Update the current span with the final output
            self._current_span.update(output=output)

            # Update the trace with the final output
            self._current_span.update_trace(output=output)

            # End the current span
            self._current_span.end()

            logging.debug("Updated observation with final output and ended span")

            # Clear current span and trace
            self._current_span = None
            self._current_trace = None

        except Exception as e:
            logging.error(f"Failed to update observation: {e}")

    def flush_traces(self) -> None:
        """Flush any pending Langfuse traces"""
        if not self._enabled or not self._client:
            return

        try:
            self._client.flush()
            logging.debug("Langfuse traces flushed successfully")
        except Exception as e:
            logging.error(f"Failed to flush Langfuse traces: {e}")

    def get_observe_decorator(self, name: str):
        """Get the observe decorator for function decoration"""
        if LANGFUSE_AVAILABLE and self._enabled:
            return observe(name=name)

        # Return no-op decorator if not available
        def decorator(func):
            return func

        return decorator


class NoOpObservabilityService:
    """No-operation observability service for when Langfuse is disabled"""

    @property
    def is_enabled(self) -> bool:
        return False

    def observe_request(self, input_data: str, metadata: dict[str, Any]) -> None:
        pass

    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        pass

    def update_observation(self, output: Any) -> None:
        pass

    def flush_traces(self) -> None:
        pass

    def get_observe_decorator(self, name: str):
        def decorator(func):
            return func

        return decorator
