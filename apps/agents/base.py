from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents in the system."""
    
    def __init__(self, name: str, model: Optional[str] = None):
        self.name = name
        self.model = model
        self.tools = []
        self.version = "0.1.0"
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary task."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return the agent's capabilities and available tools."""
        pass
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before execution."""
        return True
    
    async def log_execution(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Log execution details for audit trail."""
        logger.info(f"Agent {self.name} executed with input: {input_data}, result: {result}")