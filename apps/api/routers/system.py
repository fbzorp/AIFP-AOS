from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from apps.models.base import get_db
from apps.models.agent import AgentModel
from apps.models.task import TaskModel
from apps.models.audit_event import AuditEventModel
from apps.models.campaign import CampaignModel
from apps.models.source import SourceModel
from apps.models.content_item import ContentItemModel
from apps.agents.registry import list_agents, get_agent
from apps.api.auth import require_operator

router = APIRouter()

class CampaignCreateRequest(BaseModel):
    objective: str

class TaskCreateRequest(BaseModel):
    task_type: str
    input_data: dict

@router.get("/agents", summary="List all available agents", description="Retrieve information about all registered agents including their roles, descriptions, and capabilities.")
async def get_agents():
    agents = list_agents()
    return [
        {
            "name": a.name,
            "role": a.role,
            "description": a.description,
            "capabilities": a.get_capabilities()
        } for a in agents
    ]

@router.get("/tasks", summary="List recent tasks", description="Retrieve a list of recent task execution records with their current status.")
async def get_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).order_by(TaskModel.created_at.desc()).limit(50))
    return result.scalars().all()

@router.get("/audit")
async def get_audit(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(50))
    return result.scalars().all()

@router.get("/campaigns")
async def get_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CampaignModel).order_by(CampaignModel.created_at.desc()).limit(20))
    return result.scalars().all()

@router.post("/campaigns")
async def create_campaign(request: CampaignCreateRequest, user: dict = Depends(lambda: {"sub": "demo_user", "role": "admin"})):
    orchestrator = get_agent("Growth Orchestrator")
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Growth Orchestrator agent not found")
    
    try:
        result = await orchestrator.execute({"objective": request.objective})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks")
async def create_task(request: TaskCreateRequest, db: AsyncSession = Depends(get_db), user: dict = Depends(require_operator)):
    from apps.models.task import TaskModel
    from apps.core.audit.service import record_event
    from apps.workers.tasks import run_agent_task
    
    new_task = TaskModel(
        task_type=request.task_type,
        input_data=request.input_data,
        status="pending"
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    record_event(db, "Human", "task_created", f"Created task {new_task.id} of type {request.task_type}", {"task_id": new_task.id})
    
    # Enqueue the task
    run_agent_task.send(new_task.id)
    
    return new_task

@router.get("/sources")
async def get_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SourceModel).order_by(desc(SourceModel.relevance_score)).limit(50))
    return result.scalars().all()

# Note: GET /content moved to approvals.py for better queue management

@router.get("/metrics", summary="Get system metrics", description="Retrieve system-wide metrics including agent counts, task statistics, campaign counts, source counts, and recent audit activity.")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    # Counts
    agent_count = len(list_agents())
    
    task_stats_query = select(TaskModel.status, func.count(TaskModel.id)).group_by(TaskModel.status)
    task_stats_result = await db.execute(task_stats_query)
    task_stats = {status: count for status, count in task_stats_result.all()}
    
    campaign_count_query = select(func.count(CampaignModel.id))
    campaign_count = (await db.execute(campaign_count_query)).scalar()
    
    source_count_query = select(func.count(SourceModel.id))
    source_count = (await db.execute(source_count_query)).scalar()
    
    recent_audit_query = select(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(10)
    recent_audit = (await db.execute(recent_audit_query)).scalars().all()
    
    return {
        "agents": agent_count,
        "tasks": task_stats,
        "campaigns": campaign_count,
        "sources": source_count,
        "recent_activity": recent_audit
    }
