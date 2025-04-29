import logging
from app.models.agent import Agent

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manages the available AI agents in the system.
    In this skeleton, it uses a hardcoded list.
    In a real application, this would load from a database or configuration.
    """

    def __init__(self):
        # Placeholder agents
        # TODO: Replace with dynamic loading mechanism (DB, config file, etc.)
        self._agents: list[Agent] = [
            Agent(id="agent_001", name="EchoBot"),
            Agent(id="agent_002", name="TaskMaster"),
            Agent(id="agent_003", name="HelperAI"),
            # Add more predefined agents if needed
        ]
        # Create a dictionary for quick ID-based lookup
        self._agents_by_id: dict[str, Agent] = {
            agent.id: agent for agent in self._agents
        }
        logger.info(
            f"Initialized AgentManager with {len(self._agents)} agents: {[a.name for a in self._agents]}"
        )

    def list_agents(self) -> list[Agent]:
        """Returns a list of all available agents."""
        return self._agents

    def get_agent_by_id(self, agent_id: str) -> Agent | None:
        """Retrieves an agent by its unique ID."""
        return self._agents_by_id.get(agent_id)

    def get_default_agent(self) -> Agent | None:
        """Returns the default agent (e.g., the first one in the list)."""
        return self._agents[0] if self._agents else None


# Create a singleton instance to be used throughout the application
# This ensures all parts of the app share the same agent list/state.
agent_manager = AgentManager()
