from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from apps.models.base import get_db
from apps.models.agent import AgentModel
from apps.models.task import TaskModel
from apps.models.audit_event import AuditEventModel
from apps.models.campaign import CampaignModel
from apps.agents.registry import list_agents, get_agent

router = APIRouter()

class CampaignCreateRequest(BaseModel):
    objective: str

@router.get("/agents")
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

@router.get("/tasks")
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
async def create_campaign(request: CampaignCreateRequest):
    orchestrator = get_agent("Growth Orchestrator")
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Growth Orchestrator agent not found")
    
    try:
        result = await orchestrator.execute({"objective": request.objective})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    # Counts
    agent_count = len(list_agents())
    
    task_stats_query = select(TaskModel.status, func.count(TaskModel.id)).group_by(TaskModel.status)
    task_stats_result = await db.execute(task_stats_query)
    task_stats = {status: count for status, count in task_stats_result.all()}
    
    campaign_count_query = select(func.count(CampaignModel.id))
    campaign_count = (await db.execute(campaign_count_query)).scalar()
    
    recent_audit_query = select(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(10)
    recent_audit = (await db.execute(recent_audit_query)).scalars().all()
    
    return {
        "agents": agent_count,
        "tasks": task_stats,
        "campaigns": campaign_count,
        "recent_activity": recent_audit
    }
