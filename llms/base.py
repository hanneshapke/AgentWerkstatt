from typing import Any

from dotenv import load_dotenv

# Load environment variables once at module level
load_dotenv()

# Langfuse imports with fallback - shared by all LLM implementations
try:
    from langfuse.decorators import langfuse_context, observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

    # Create dummy decorators if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator if args else decorator

    # Create dummy langfuse_context
    class DummyLangfuseContext:
        def update_current_observation(self, **kwargs):
            pass

        def update_current_span(self, **kwargs):
            pass

    langfuse_context = DummyLangfuseContext()


class BaseLLM:
    """Abstract base class for all LLMs"""

    def __init__(self, model_name: str, tools: dict[str, Any], agent_objective: str = ""):
        self.model_name = model_name
        self.api_key = ""
        self.base_url = ""
        self.conversation_history = []
        self.agent_objective = agent_objective
        self.base_system_prompt = ""
        self.tools = tools
        self.timeout = 30.0

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def _format_tool_descriptions(self) -> str:
        """Format tool descriptions for system prompt"""
        if not self.tools:
            return "No tools available."

        tool_descriptions = ""
        for tool in self.tools:
            tool_descriptions += (
                f"{tool.get_name()} ({tool.get_function_name()}): {tool.description}\n"
            )
        return tool_descriptions.strip()

    def _get_default_system_prompt_template(self) -> str:
        """Get the default system prompt template"""
        return """
{agent_objective}

You have {num_tools} tools at your disposal:

{tool_descriptions}
""".strip()

    def _format_system_prompt(self, template: str = None) -> str:
        """Format the system prompt with agent objective and tools"""
        if template is None:
            template = self._get_default_system_prompt_template()

        return template.format(
            agent_objective=self.agent_objective,
            num_tools=len(self.tools),
            tool_descriptions=self._format_tool_descriptions(),
        )

    def _validate_api_key(self, api_key_name: str) -> None:
        """Validate that API key is set, raise error if not"""
        if not self.api_key:
            raise ValueError(f"{api_key_name} environment variable is required")

    def _get_tool_schemas(self) -> list[dict]:
        """Get tool schemas for API calls"""
        return [tool.get_schema() for tool in self.tools] if self.tools else []

    def _update_langfuse_observation(self, **kwargs) -> None:
        """Update Langfuse observation if available and has active context"""
        if LANGFUSE_AVAILABLE:
            try:
                langfuse_context.update_current_observation(**kwargs)
            except Exception:
                # Silently handle cases where there's no active span context
                # This can happen when @observe decorators aren't properly set up
                # or when called outside of an observed function
                pass

    def make_api_request(self, messages: list[dict]) -> str:
        """Make an API request to the LLM"""
        raise NotImplementedError("Subclasses must implement this method")

    def process_request(self, messages: list[dict]) -> tuple[list[dict], list]:
        """Process user request using LLM

        Args:
            messages: List of conversation messages

        Returns:
            Tuple of (updated_messages, assistant_message_content)
        """
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return self.base_system_prompt
