"""
Google ADK-based Marketing Manager root agent.
This agent uses ADK's LlmAgent and Runner to intelligently route tasks to specialized agents.
"""

import logging
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.tools import FunctionTool
from apps.core.models.factory import deepseek_reasoning
from apps.agents.registry import get_agent
from apps.core.audit.service import record_event
from apps.models.base import SessionLocal

logger = logging.getLogger(__name__)

# Marketing Manager root agent instruction
MARKETING_MANAGER_INSTRUCTION = """
You are the Marketing Manager, responsible for orchestrating marketing campaigns across multiple specialized agents.

Available specialists and their roles:
1. Market Intelligence - Researches and discovers relevant market trends, discussions, and opportunities
2. Content Strategy - Plans content strategy and editorial calendar based on intelligence
3. Technical Content - Creates technical documentation, tutorials, and developer-focused content
4. Founder Content - Creates founder-led content, announcements, and thought leadership pieces
5. SEO Content - Creates Google-search-optimized long-form content with SEO metadata (title tag, meta description, keywords, H1/H2 structure)
6. Social Publishing - Manages social media publishing and distribution (can publish to Moltbook)
7. Community Engagement - Handles community interactions, discussions, and engagement proposals (can publish to Moltbook)
8. Analytics - Tracks content performance and provides insights
9. Compliance & Brand - Ensures content meets brand guidelines and compliance requirements

When given a marketing objective, determine the optimal sequence of specialist agents to involve.
For content creation campaigns, typically: Market Intelligence -> Content Strategy -> Technical/Founder/SEO Content -> Compliance & Brand -> Social Publishing
For SEO-focused campaigns: Market Intelligence -> Content Strategy -> SEO Content -> Compliance & Brand
For community-focused campaigns: Market Intelligence -> Community Engagement -> Social Publishing
For analytics and optimization: Market Intelligence -> Analytics

Respond with a JSON array of steps, where each step has:
- "agent": the specialist name
- "input": the input data for that specialist
- "reason": brief reasoning for this step
"""

class ADKOrchestrator:
    """ADK-based orchestrator using Marketing Manager root agent."""
    
    def __init__(self):
        self.root_agent = None
        self.runner = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the ADK Marketing Manager root agent."""
        if self._initialized:
            return True
        
        # Get DeepSeek model for the root agent
        model = deepseek_reasoning()
        if model is None:
            logger.warning("DEEPSEEK_API_KEY not available, ADK orchestrator will use static fallback")
            return False
        
        try:
            # Create specialist tools
            tools = self.create_specialist_tools()
            
            # Create Marketing Manager root agent with tools
            self.root_agent = LlmAgent(
                name="marketing_manager",
                model=model,
                instruction=MARKETING_MANAGER_INSTRUCTION,
                tools=tools
            )
            
            # Create ADK Runner
            self.runner = Runner(self.root_agent)
            
            self._initialized = True
            logger.info("ADK Marketing Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ADK orchestrator: {e}")
            return False
    
    def create_specialist_tools(self) -> List[FunctionTool]:
        """Create ADK tools for each specialist agent."""
        tools = []
        
        specialist_names = [
            "Market Intelligence",
            "Content Strategy", 
            "Technical Content",
            "Founder Content",
            "SEO Content",
            "Social Publishing",
            "Community Engagement",
            "Analytics",
            "Compliance & Brand"
        ]
        
        for specialist_name in specialist_names:
            # Create a wrapper function with proper metadata
            # Use default argument to capture the variable correctly
            async def specialist_wrapper(input_data: Dict[str, Any] = None, specialist=specialist_name) -> Dict[str, Any]:
                return self._execute_specialist(specialist, input_data)
            
            specialist_wrapper.__name__ = f"run_{specialist_name.lower().replace(' ', '_')}"
            specialist_wrapper.__doc__ = f"Execute {specialist_name} specialist agent"
            
            tool = FunctionTool(func=specialist_wrapper)
            tools.append(tool)
        
        return tools
    
    def _execute_specialist(self, specialist_name: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specialist agent via the existing BaseAgent.execute interface."""
        if input_data is None:
            input_data = {}
        
        try:
            agent = get_agent(specialist_name)
            if agent is None:
                return {"error": f"Specialist '{specialist_name}' not found"}
            
            # Execute the specialist (preserves existing persistence/audit/approval logic)
            # Handle async execution in both sync and async contexts
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to run in a thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, agent.execute(input_data))
                    result = future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                result = asyncio.run(agent.execute(input_data))
            
            return {"specialist": specialist_name, "result": result}
            
        except Exception as e:
            logger.error(f"Error executing specialist {specialist_name}: {e}")
            return {"error": str(e), "specialist": specialist_name}
    
    async def orchestrate_campaign(self, objective: str, db_session = None) -> Dict[str, Any]:
        """
        Orchestrate a campaign using ADK Marketing Manager or static fallback.
        
        Returns the ordered list of specialist steps for the campaign.
        """
        from apps.models.base import get_sync_session
        
        # Use provided session or create new one
        if db_session is None:
            session_provided = False
            db_session = SessionLocal()
        else:
            session_provided = True
        
        try:
            # Try to use ADK routing if available
            if self.initialize():
                try:
                    logger.info(f"Using ADK Marketing Manager to orchestrate campaign: {objective}")
                    
                    # Run the Marketing Manager via ADK Runner
                    user_message = f"Plan a marketing campaign for the following objective: {objective}"
                    response = await self.runner.run_async(user_message=user_message)
                    
                    # Parse the response to extract steps
                    steps = self._parse_adk_response(response)
                    
                    # Record audit event for ADK routing
                    try:
                        record_event(
                            db_session,
                            agent_name="Marketing Manager (ADK)",
                            event_type="campaign_orchestrated",
                            message=f"ADK-routed campaign: {objective}",
                            metadata={"objective": objective, "routing_method": "adk_routed", "steps": steps}
                        )
                        db_session.commit()
                    except Exception as e:
                        logger.error(f"Failed to record audit event: {e}")
                        if hasattr(db_session, 'rollback'):
                            db_session.rollback()
                    finally:
                        if not session_provided and hasattr(db_session, 'close'):
                            db_session.close()
                    
                    return {
                        "routing_method": "adk_routed",
                        "steps": steps,
                        "objective": objective
                    }
                    
                except Exception as e:
                    logger.error(f"ADK orchestration failed, falling back to static: {e}")
                    return self._static_fallback(objective, db_session, session_provided)
            else:
                logger.info("ADK not available, using static fallback for campaign orchestration")
                return self._static_fallback(objective, db_session, session_provided)
        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            if not session_provided and hasattr(db_session, 'close'):
                db_session.close()
            raise
    
    def _parse_adk_response(self, response: Any) -> List[Dict[str, Any]]:
        """Parse ADK response to extract the ordered list of specialist steps."""
        # This is a simplified parser - in production, you'd want more robust parsing
        # The ADK agent should return a JSON array of steps
        try:
            # Extract the content from the ADK response
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, dict) and 'content' in response:
                content = response['content']
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            # Try to parse JSON from the response
            import json
            import re
            
            # Look for JSON array in the response
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group(0))
                if isinstance(steps, list):
                    return steps
            
            # Fallback: parse steps from text
            logger.warning("Could not parse JSON from ADK response, using static fallback")
            return self._get_static_steps()
            
        except Exception as e:
            logger.error(f"Error parsing ADK response: {e}")
            return self._get_static_steps()
    
    def _static_fallback(self, objective: str, db_session, session_provided: bool = False) -> Dict[str, Any]:
        """Static fallback orchestration when ADK is not available."""
        logger.info(f"Using static fallback for campaign: {objective}")
        
        steps = self._get_static_steps()
        
        # Record audit event for static fallback
        try:
            record_event(
                db_session,
                agent_name="Growth Orchestrator (Static)",
                event_type="campaign_orchestrated",
                message=f"Static-fallback campaign: {objective}",
                metadata={"objective": objective, "routing_method": "static_fallback", "steps": steps}
            )
            if not session_provided:
                db_session.commit()
        except Exception as e:
            logger.error(f"Failed to record audit event: {e}")
            if not session_provided and hasattr(db_session, 'rollback'):
                db_session.rollback()
        finally:
            if not session_provided and hasattr(db_session, 'close'):
                db_session.close()
        
        return {
            "routing_method": "static_fallback",
            "steps": steps,
            "objective": objective
        }
    
    def _get_static_steps(self) -> List[Dict[str, Any]]:
        """Get the static list of specialist steps (fallback)."""
        return [
            {"agent": "Market Intelligence", "input": {"topic": "campaign"}, "reason": "Research market trends and opportunities"},
            {"agent": "Content Strategy", "input": {"objective": "campaign"}, "reason": "Plan content strategy and calendar"},
            {"agent": "SEO Content", "input": {"objective": "campaign"}, "reason": "Create Google-optimized content"},
            {"agent": "Community Engagement", "input": {"objective": "campaign"}, "reason": "Handle community interactions and discussions"}
        ]

# Singleton instance
_adk_orchestrator = ADKOrchestrator()

def get_adk_orchestrator() -> ADKOrchestrator:
    """Get the singleton ADK orchestrator instance."""
    return _adk_orchestrator
