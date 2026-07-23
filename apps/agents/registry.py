from __future__ import annotations
from typing import Dict, List, Type
from .base import BaseAgent

class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._initialized = False
    
    def register(self, agent_cls: Type[BaseAgent]) -> None:
        name = getattr(agent_cls, 'name', agent_cls.__name__)
        self._agents[name] = agent_cls
        
    def register_default_agents(self) -> None:
        """
        Lazily registers all default specialized agents.
        This method is idempotent via the self._initialized guard.
        """
        if self._initialized:
            return
            
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
        self._initialized = True
            
    def ensure_initialized(self) -> None:
        """Internal alias for lazy initialization."""
        self.register_default_agents()
            
    def list_agents(self) -> List[BaseAgent]:
        self.ensure_initialized()
        return [agent_cls() for agent_cls in self._agents.values()]
        
    def get_agent(self, name: str) -> BaseAgent | None:
        self.ensure_initialized()
        agent_cls = self._agents.get(name)
        return agent_cls() if agent_cls else None

# Singleton instance - LAZY: do NOT call register_default_agents() here
_registry = AgentRegistry()

def list_agents() -> List[BaseAgent]:
    """Module-level helper to list all registered agents."""
    return _registry.list_agents()

def get_agent(name: str) -> BaseAgent | None:
    """Module-level helper to get an agent by name."""
    return _registry.get_agent(name)
