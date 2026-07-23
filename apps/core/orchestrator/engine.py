import logging
from sqlalchemy.orm import Session
from apps.models.task import TaskModel
from apps.models.campaign import CampaignModel
from apps.core.audit.service import record_event

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, session: Session):
        self.session = session

    async def create_campaign(self, objective: str, steps: list):
        """
        Creates a campaign and its associated tasks, then enqueues them.
        """
        # Lazy import to break circular dependency with tasks.py
        from apps.workers.tasks import run_agent_task
        
        campaign = CampaignModel(
            name=f"Campaign: {objective[:30]}...",
            objective=objective,
            status="running"
        )
        self.session.add(campaign)
        self.session.flush()
        
        record_event(self.session, "GrowthOrchestrator", "campaign_created", f"Created campaign for: {objective}", {"campaign_id": campaign.id})
        
        tasks = []
        for step in steps:
            task = TaskModel(
                task_type=step.get("agent", "Market Intelligence"),
                input_data=step.get("input", {}),
                status="pending"
            )
            self.session.add(task)
            self.session.flush()
            tasks.append(task)
            
            # Enqueue task
            run_agent_task.send(task.id)
            record_event(self.session, "GrowthOrchestrator", "task_enqueued", f"Enqueued {task.task_type} for campaign", {"task_id": task.id, "campaign_id": campaign.id})
            
        return {
            "campaign_id": campaign.id,
            "tasks": [t.id for t in tasks]
        }
