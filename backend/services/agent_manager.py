import logging

from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse

from backend.models.llm_agent import LLMAgent

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manages the available AI agents in the system.
    In this skeleton, it uses a hardcoded list.
    In a real application, this would load from a database or configuration.
    """

    def __init__(self):
        self._agents: list[LLMAgent] = []
        # Create a dictionary for quick ID-based lookup
        self._agents_by_id: dict[str, LLMAgent] = {}

    def list_agents(self) -> list[LLMAgent]:
        """Returns a list of all available agents."""
        return self._agents

    def get_agent_by_id(self, agent_id: str) -> LLMAgent | None:
        """Retrieves an agent by its unique ID."""
        return self._agents_by_id.get(agent_id)

    def get_default_agent(self) -> LLMAgent | None:
        """Returns the default agent (e.g., the first one in the list)."""
        return self._agents[0] if self._agents else None

    def add_agent(self, agent: LLMAgent):
        """Adds a new agent to the list."""
        self._agents.append(agent)
        self._agents_by_id[agent.id] = agent

    async def run(self, prompt: str, agent_id: str) -> ModelResponse:
        """Async run the user prompt"""
        raise NotImplementedError


# Create a singleton instance to be used throughout the application
# This ensures all parts of the app share the same agent list/state.
agent_manager = AgentManager()
