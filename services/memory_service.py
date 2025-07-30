import logging

from ..config import AgentConfig

# mem0 imports
try:
    from mem0 import Memory

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False


class MemoryService:
    """Service for handling memory operations using mem0"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._memory: Memory | None = None
        self._enabled = False
        self._initialize_memory()

    @property
    def is_enabled(self) -> bool:
        """Check if memory service is enabled and available"""
        return self._enabled

    def _initialize_memory(self) -> None:
        """Initialize mem0 if enabled and available"""
        print(f"🧠 Memory setup - MEM0_AVAILABLE: {MEM0_AVAILABLE}")
        print(f"🧠 Memory setup - config.memory_enabled: {self.config.memory_enabled}")

        if not MEM0_AVAILABLE:
            if self.config.memory_enabled:
                logging.warning(
                    "Memory is enabled in config but mem0 is not installed. Install with: pip install mem0ai"
                )
            print("❌ mem0 not available")
            return

        if not self.config.memory_enabled:
            logging.debug("Memory system is disabled")
            print("❌ Memory disabled in config")
            return

        try:
            # Initialize mem0 with server URL if provided
            if (
                self.config.memory_server_url
                and self.config.memory_server_url != "http://localhost:8000"
            ):
                # If custom server URL is provided, use it
                self._memory = Memory(config={"server_url": self.config.memory_server_url})
            else:
                # Use default initialization (will use local or default server)
                self._memory = Memory()

            self._enabled = True
            logging.info(
                f"mem0 memory system initialized successfully. Server: {self.config.memory_server_url}"
            )
            print("✅ Memory setup completed successfully!")

        except Exception as e:
            logging.error(f"Failed to initialize mem0: {e}")
            print(f"❌ Memory setup failed: {e}")
            print(
                "💡 Make sure mem0 service is running: docker compose -f third_party/docker-compose.yaml up -d mem0"
            )
            self._enabled = False

    def retrieve_memories(self, user_input: str, user_id: str) -> str:
        """Retrieve relevant memories for the user input"""
        if not self._enabled or not self._memory:
            return ""

        try:
            relevant_memories = self._memory.search(query=user_input, user_id=user_id, limit=3)

            if not relevant_memories.get("results"):
                return ""

            memories_str = "\n".join(
                f"- {entry['memory']}" for entry in relevant_memories["results"]
            )
            return f"\nRelevant memories:\n{memories_str}\n"

        except Exception as e:
            logging.error(f"Failed to retrieve memories: {e}")
            return ""

    def store_conversation(self, user_input: str, assistant_response: str, user_id: str) -> None:
        """Store the conversation in memory"""
        if not self._enabled or not self._memory:
            return

        try:
            messages = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_response},
            ]

            self._memory.add(messages, user_id=user_id)
            logging.debug("Conversation stored in memory successfully")

        except Exception as e:
            logging.error(f"Failed to store conversation in memory: {e}")


class NoOpMemoryService:
    """No-operation memory service for when memory is disabled"""

    @property
    def is_enabled(self) -> bool:
        return False

    def retrieve_memories(self, user_input: str, user_id: str) -> str:
        return ""

    def store_conversation(self, user_input: str, assistant_response: str, user_id: str) -> None:
        pass
