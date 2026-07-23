from __future__ import annotations
from typing import Dict, List, Type
from .base import BaseAgent

class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, Type[BaseAgent]] = {}
    
    def register(self, agent_cls: Type[BaseAgent]) -> None:
        # Use either class name or a name attribute if it exists
        name = getattr(agent_cls, 'name', agent_cls.__name__)
        self._agents[name] = agent_cls
        
    def register_default_agents(self) -> None:
        from .specialized import (
            GrowthOrchestratorAgent, 
            MarketIntelligenceAgent, 
            ContentStrategyAgent, 
            TechnicalContentAgent, 
            FounderContentAgent, 
            SocialPublishingAgent, 
            CommunityEngagementAgent, 
            AnalyticsAgent, 
            ComplianceBrandAgent
        )
        for cls in [
            GrowthOrchestratorAgent, 
            MarketIntelligenceAgent, 
            ContentStrategyAgent, 
            TechnicalContentAgent, 
            FounderContentAgent, 
            SocialPublishingAgent, 
            CommunityEngagementAgent, 
            AnalyticsAgent, 
            ComplianceBrandAgent
        ]:
            self.register(cls)
            
    def list_agents(self) -> List[BaseAgent]:
        return [agent_cls() for agent_cls in self._agents.values()]
        
    def get_agent(self, name: str) -> BaseAgent | None:
        agent_cls = self._agents.get(name)
        return agent_cls() if agent_cls else None

# Singleton instance
_registry = AgentRegistry()
_registry.register_default_agents()

def list_agents() -> List[BaseAgent]:
    """Module-level helper to list all registered agents."""
    return _registry.list_agents()

def get_agent(name: str) -> BaseAgent | None:
    """Module-level helper to get an agent by name."""
    return _registry.get_agent(name)
