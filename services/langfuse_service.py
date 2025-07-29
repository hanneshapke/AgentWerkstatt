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

    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Observe tool execution by creating a child generation that can be updated later"""
        if not self._enabled or not self._client or not self._current_span:
            return None

        try:
            # Create a child generation for tool execution - similar to LLM calls
            # This allows us to update it with actual results later
            tool_generation = self._current_span.start_generation(
                name=f"Tool: {tool_name}",
                input=tool_input,
                metadata={"tool_name": tool_name, "type": "tool_execution"},
            )

            logging.debug(f"Created tool generation for {tool_name}, type: {type(tool_generation)}")
            return tool_generation

        except Exception as e:
            logging.error(f"Failed to observe tool execution: {e}")
            return None

    def update_tool_observation(self, tool_generation: Any, output: Any) -> None:
        """Update a tool generation with output data"""
        if not self._enabled or not tool_generation:
            return

        try:
            logging.debug(f"Updating tool observation with output: {type(output)}")
            tool_generation.update(output=output)
            tool_generation.end()
            logging.debug("Successfully updated and ended tool generation")

        except Exception as e:
            logging.error(f"Failed to update tool observation: {e}")
            # Re-raise the exception to make debugging easier
            raise

    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] = None
    ) -> Any:
        """Create a generation for LLM API calls"""
        if not self._enabled or not self._client or not self._current_span:
            return None

        try:
            # Create a child generation using the current span - manual pattern for later updates
            llm_generation = self._current_span.start_generation(
                name=f"LLM Call: {model_name}",
                input=messages,
                model=model_name,
                metadata={"type": "llm_call", **(metadata or {})},
            )

            logging.debug(f"Created LLM generation for {model_name}, type: {type(llm_generation)}, has update: {hasattr(llm_generation, 'update')}")
            return llm_generation

        except Exception as e:
            logging.error(f"Failed to observe LLM call: {e}")
            return None

    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] = None
    ) -> None:
        """Update an LLM generation with output and usage data"""
        logging.debug(f"update_llm_observation called - enabled: {self._enabled}, llm_generation: {llm_generation is not None}")

        if llm_generation is not None:
            logging.debug(f"LLM generation type: {type(llm_generation)}, has update: {hasattr(llm_generation, 'update')}, has end: {hasattr(llm_generation, 'end')}")

        if not self._enabled:
            logging.debug("Langfuse service not enabled, skipping LLM observation update")
            return

        if not llm_generation:
            logging.debug("No LLM generation provided, skipping LLM observation update")
            return

        try:
            update_data = {"output": output}
            if usage:
                update_data["usage_details"] = usage  # v3 uses usage_details
                logging.debug(f"Updating LLM generation with usage: {usage}")
            else:
                logging.debug("Updating LLM generation without usage data")

            llm_generation.update(**update_data)
            llm_generation.end()

            logging.debug("Successfully updated LLM generation with output and usage")

        except Exception as e:
            logging.error(f"Failed to update LLM observation: {e}")
            # Re-raise the exception to make debugging easier
            raise

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
            logging.debug("Langfuse service not enabled or no client, skipping flush")
            return

        try:
            logging.debug("Flushing Langfuse traces...")
            self._client.flush()
            logging.debug("Langfuse traces flushed successfully")
        except Exception as e:
            logging.error(f"Failed to flush Langfuse traces: {e}")
            # Re-raise the exception to make debugging easier
            raise

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

    def observe_tool_execution(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        return None

    def update_tool_observation(self, tool_observation: Any, output: Any) -> None:
        pass

    def observe_llm_call(
        self, model_name: str, messages: list[dict], metadata: dict[str, Any] = None
    ) -> Any:
        return None

    def update_llm_observation(
        self, llm_generation: Any, output: Any, usage: dict[str, Any] = None
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
