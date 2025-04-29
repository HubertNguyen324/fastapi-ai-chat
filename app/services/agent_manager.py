from typing import List
from app.models.agent import Agent
import uuid


class AgentManager:
    def __init__(self):
        # Placeholder agents - replace with DB loading later
        self._agents: List[Agent] = [
            Agent(id="agent_001", name="EchoBot"),
            Agent(id="agent_002", name="TaskMaster"),
            Agent(id="agent_003", name="HelperAI"),
        ]
        self._agents_by_id = {agent.id: agent for agent in self._agents}

    def list_agents(self) -> List[Agent]:
        return self._agents

    def get_agent_by_id(self, agent_id: str) -> Agent | None:
        return self._agents_by_id.get(agent_id)

    def get_default_agent(self) -> Agent | None:
        return self._agents[0] if self._agents else None


# Singleton instance
agent_manager = AgentManager()
