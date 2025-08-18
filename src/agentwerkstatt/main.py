from absl import logging

from .config import AgentConfig
from .interfaces import (
    ConversationHandlerProtocol,
    MemoryServiceProtocol,
    ObservabilityServiceProtocol,
    ToolExecutorProtocol,
)
from .llms import (
    create_claude_llm,
    create_gpt_oss_llm,
    create_ollama_llm,
    create_lmstudio_llm,
    create_gemini_llm,
)
from .llms.base import BaseLLM
from .services.conversation_handler import ConversationHandler
from .services.langfuse_service import LangfuseService, NoOpObservabilityService
from .services.memory_service import MemoryService, NoOpMemoryService
from .services.tool_executor import ToolExecutor
from .services.tool_interaction_handler import ToolInteractionHandler
from .tools.discovery import ToolRegistry


# Map LLM provider names to their factory functions
LLM_FACTORIES = {
    "claude": create_claude_llm,
    "gpt-oss": create_gpt_oss_llm,
    "ollama": create_ollama_llm,
    "lmstudio": create_lmstudio_llm,
    "gemini": create_gemini_llm,
}


class Agent:
    """
    Refactored minimalistic agent with dependency injection and separation of concerns
    """

    def __init__(
        self,
        config: AgentConfig,
        llm: BaseLLM | None = None,
        memory_service: MemoryServiceProtocol | None = None,
        observability_service: ObservabilityServiceProtocol | None = None,
        tool_executor: ToolExecutorProtocol | None = None,
        conversation_handler: ConversationHandlerProtocol | None = None,
        session_id: str | None = None,
    ):
        self.config = config
        self.session_id = session_id

        default_persona_config = next(
            (p for p in config.personas if p.id == config.default_persona), None
        )
        if not default_persona_config:
            raise ValueError(
                f"Default persona '{config.default_persona}' not found in configuration."
            )

        self.active_persona_name = default_persona_config.id
        self.active_persona = default_persona_config.file

        # Corrected Initialization Order
        # 1. Initialize services without LLM or tool dependencies
        self.memory_service = memory_service or self._create_memory_service()
        self.observability_service = observability_service or self._create_observability_service()

        # 2. Initialize LLM, but without tools for now
        self.llm = llm or self._create_llm()

        # 3. Initialize tool registry, injecting the LLM and config
        self.tool_registry = ToolRegistry(
            tools_dir=config.tools_dir, llm_client=self.llm, agent_config=self.config
        )
        self.tools = self.tool_registry.get_tools()

        # 4. Now, provide the tools to the LLM instance to break the circular dependency
        self.llm.tools = self.tools

        # 5. Initialize remaining services
        self.tool_executor = tool_executor or self._create_tool_executor()
        self.tool_interaction_handler = self._create_tool_interaction_handler()
        self.conversation_handler = conversation_handler or self._create_conversation_handler()

        self._set_logging_verbosity(self.config.verbose)

        logging.debug(f"Tools: {self.tools}")

    def _set_logging_verbosity(self, verbose: bool):
        """Set logging verbosity based on config"""
        if verbose:
            logging.set_verbosity(logging.DEBUG)
        else:
            logging.set_verbosity(logging.WARNING)

    def _create_llm(self) -> BaseLLM:
        """Create LLM based on configuration and active persona"""
        provider = self.config.llm.provider
        factory = LLM_FACTORIES.get(provider)
        if not factory:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        return factory(
            persona=self.active_persona,
            model_name=self.config.llm.model,
            observability_service=self.observability_service,
        )

    def switch_persona(self, persona_name: str):
        """Switches the agent's active persona."""
        persona_config = next((p for p in self.config.personas if p.id == persona_name), None)
        if not persona_config:
            raise ValueError(f"Persona '{persona_name}' not found in configuration.")

        self.active_persona_name = persona_config.id
        self.active_persona = persona_config.file

        # Update the LLM with the new persona
        self.llm.set_persona(self.active_persona)
        logging.info(f"Switched to persona: {persona_name}")

    def _create_memory_service(self) -> MemoryServiceProtocol:
        """Create memory service based on configuration"""
        if self.config.memory.enabled:
            return MemoryService(self.config)
        return NoOpMemoryService()

    def _create_observability_service(self) -> ObservabilityServiceProtocol:
        """Create observability service based on configuration"""
        if self.config.langfuse.enabled:
            return LangfuseService(self.config)
        return NoOpObservabilityService()

    def _create_tool_executor(self) -> ToolExecutorProtocol:
        """Create tool executor with observability support"""
        return ToolExecutor(self.tool_registry, self.observability_service, agent_instance=self)

    def _create_tool_interaction_handler(self) -> ToolInteractionHandler:
        """Create tool interaction handler."""
        return ToolInteractionHandler(self.tool_executor)

    def _create_conversation_handler(self) -> ConversationHandlerProtocol:
        """Create conversation handler with all dependencies"""
        return ConversationHandler(
            llm=self.llm,
            agent=self,
            memory_service=self.memory_service,
            observability_service=self.observability_service,
            tool_interaction_handler=self.tool_interaction_handler,
        )

    def process_request(self, user_input: str, session_id: str | None = None) -> str:
        """
        Process user request using the conversation handler

        Args:
            user_input: User's request as a string
            session_id: Optional session ID to group related traces

        Returns:
            Response string from the agent
        """

        # Use provided session_id or fall back to instance session_id
        current_session_id = session_id or self.session_id

        # Start observing the request
        metadata = {
            "model": self.llm.model_name,
            "project": self.config.langfuse.project_name,
            "memory_enabled": self.memory_service.is_enabled,
            "session_id": current_session_id,
        }
        self.observability_service.observe_request(user_input, metadata)

        # Enhance input with memory context
        enhanced_input = self.conversation_handler.enhance_input_with_memory(user_input)

        # Process the message
        response = self.conversation_handler.process_message(user_input, enhanced_input)

        return response


def run_agent(config: AgentConfig, session_id: str | None = None):
    """
    Initializes and runs the agent based on the provided configuration.
    """
    agent = Agent(config=config, session_id=session_id)
    print(f"Starting agent with persona: {agent.active_persona_name}")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting.")
            break

        if user_input.startswith("/persona "):
            persona_name = user_input.split(" ", 1)[1]
            try:
                agent.switch_persona(persona_name)
                print(f"Switched to persona: {persona_name}")
            except ValueError as e:
                print(e)
            continue

        response = agent.process_request(user_input)
        print(f"Agent: {response}")
