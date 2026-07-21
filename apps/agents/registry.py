from __future__ import annotations

from typing import Dict, List, Type

from .base import BaseAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, Type[BaseAgent]] = {}

    def register(self, agent_cls: Type[BaseAgent]) -> None:
        self._agents[agent_cls.__name__] = agent_cls

    def register_default_agents(self) -> None:
        from .specialized import GrowthOrchestratorAgent, MarketIntelligenceAgent, ContentStrategyAgent

        self.register(GrowthOrchestratorAgent)
        self.register(MarketIntelligenceAgent)
        self.register(ContentStrategyAgent)

    def list_agents(self) -> List[BaseAgent]:
        return [agent_cls() for agent_cls in self._agents.values()]

    def get_agent(self, name: str) -> BaseAgent | None:
        agent_cls = self._agents.get(name)
        return agent_cls() if agent_cls else None
