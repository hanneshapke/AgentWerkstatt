from absl import logging

from config import AgentConfig
from interfaces import (
    ConversationHandlerProtocol,
    MemoryServiceProtocol,
    ObservabilityServiceProtocol,
    ToolExecutorProtocol,
)
from llms.base import BaseLLM
from llms.claude import ClaudeLLM
from services.conversation_handler import ConversationHandler
from services.langfuse_service import LangfuseService, NoOpObservabilityService
from services.memory_service import MemoryService, NoOpMemoryService
from services.tool_executor import ToolExecutor
from tools.discovery import ToolRegistry


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
        self.active_persona_name = config.default_persona
        self.active_persona = self.config.personas[self.active_persona_name]

        # Initialize tool registry first
        self.tool_registry = ToolRegistry(tools_dir=config.tools_dir)
        self.tools = self.tool_registry.get_tools()

        # Initialize services first (order matters for dependencies)
        self.memory_service = memory_service or self._create_memory_service()
        self.observability_service = observability_service or self._create_observability_service()

        # Initialize LLM after observability service is available
        self.llm = llm or self._create_llm()

        # Initialize remaining services
        self.tool_executor = tool_executor or self._create_tool_executor()
        self.conversation_handler = conversation_handler or self._create_conversation_handler()

        self._set_logging_verbosity(self.config.verbose)

        logging.debug(f"Tools: {self.tools}")

    def _set_logging_verbosity(self, verbose: bool):
        """Set logging verbosity based on config"""
        if verbose:
            logging.set_verbosity(logging.DEBUG)
        else:
            logging.set_verbosity(logging.ERROR)

    def _create_llm(self) -> BaseLLM:
        """Create LLM based on configuration and active persona"""
        return ClaudeLLM(
            persona=self.active_persona,  # Use active_persona
            model_name=self.config.model,
            tools=self.tools,
            observability_service=self.observability_service,
        )

    def switch_persona(self, persona_name: str):
        """Switches the agent's active persona."""
        if persona_name not in self.config.personas:
            raise ValueError(f"Persona '{persona_name}' not found in configuration.")

        self.active_persona_name = persona_name
        self.active_persona = self.config.personas[persona_name]

        # Update the LLM with the new persona
        self.llm.set_persona(self.active_persona)
        logging.info(f"Switched to persona: {persona_name}")

    def _create_memory_service(self) -> MemoryServiceProtocol:
        """Create memory service based on configuration"""
        if self.config.memory_enabled:
            return MemoryService(self.config)
        return NoOpMemoryService()

    def _create_observability_service(self) -> ObservabilityServiceProtocol:
        """Create observability service based on configuration"""
        if self.config.langfuse_enabled:
            return LangfuseService(self.config)
        return NoOpObservabilityService()

    def _create_tool_executor(self) -> ToolExecutorProtocol:
        """Create tool executor with observability support"""
        return ToolExecutor(self.tool_registry, self.observability_service, agent_instance=self)

    def _create_conversation_handler(self) -> ConversationHandlerProtocol:
        """Create conversation handler with all dependencies"""
        return ConversationHandler(
            llm=self.llm,
            agent=self,
            memory_service=self.memory_service,
            observability_service=self.observability_service,
            tool_executor=self.tool_executor,
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
            "project": self.config.langfuse_project_name,
            "memory_enabled": self.memory_service.is_enabled,
            "session_id": current_session_id,
        }
        self.observability_service.observe_request(user_input, metadata)

        # Enhance input with memory context
        enhanced_input = self.conversation_handler.enhance_input_with_memory(user_input)

        # Process the message
        response = self.conversation_handler.process_message(user_input, enhanced_input)

        return response
