import logging
from sqlalchemy.orm import Session
from apps.models.task import TaskModel
from apps.models.campaign import CampaignModel
from apps.core.audit.service import record_event

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, session: Session):
        self.session = session

    def create_campaign(self, objective: str, steps: list):
        """
        Creates a campaign and its associated tasks, then enqueues them.
        Ensures all DB rows are committed before enqueuing to avoid worker race conditions.
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
            tasks.append(task)
        
        # Flush to get task IDs
        self.session.flush()
        
        # Record task_enqueued events BEFORE commit
        for task in tasks:
            record_event(
                self.session, 
                "GrowthOrchestrator", 
                "task_enqueued", 
                f"Enqueued {task.task_type} for campaign: {task.id}", 
                {"task_id": task.id, "campaign_id": campaign.id, "task_type": task.task_type}
            )
        
        # Commit now so the worker can definitely see the rows
        self.session.commit()
        
        # Enqueue tasks AFTER commit
        for task in tasks:
            run_agent_task.send(task.id)
            logger.info(f"Enqueued {task.task_type} for campaign {campaign.id}, task_id: {task.id}")
            
        return {
            "campaign_id": campaign.id,
            "tasks": [t.id for t in tasks]
        }
