from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apps.models.base import get_db
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.models.audit_event import AuditEventModel
from apps.core.policy.engine import compute_draft_hash
from apps.core.audit.service import record_event
from apps.workers.tasks import publish_content

router = APIRouter()

class ApprovalDecisionRequest(BaseModel):
    approved_by: str
    expires_in_hours: Optional[int] = 24
    reason: Optional[str] = None

@router.get("/approvals")
async def list_approvals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApprovalModel).order_by(ApprovalModel.created_at.desc()).limit(50))
    return result.scalars().all()

@router.post("/content/{content_id}/submit")
async def submit_content(content_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentItemModel).filter(ContentItemModel.id == content_id))
    content = result.scalars().first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    content.status = "pending_review"
    await db.commit()
    return {"status": "pending_review", "content_id": content_id}

@router.post("/content/{content_id}/approve")
async def approve_content(content_id: str, request: ApprovalDecisionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentItemModel).filter(ContentItemModel.id == content_id))
    content = result.scalars().first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    draft_hash = compute_draft_hash(content)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=request.expires_in_hours)
    
    approval = ApprovalModel(
        content_id=content_id,
        draft_hash=draft_hash,
        status="approved",
        approved_by=request.approved_by,
        expires_at=expires_at,
        decided_at=now
    )
    db.add(approval)
    await db.flush() # Get approval.id
    
    content.status = "approved"
    
    # Record audit event
    record_event(
        db, 
        agent_name=request.approved_by or "Human", 
        event_type="content_approved", 
        message=f"Content approved: {content.title}",
        metadata={"content_id": content_id, "approval_id": approval.id, "draft_hash": draft_hash}
    )
    
    await db.commit()
    return {
        "approval_id": approval.id,
        "draft_hash": draft_hash,
        "status": "approved"
    }

@router.post("/content/{content_id}/reject")
async def reject_content(content_id: str, request: ApprovalDecisionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentItemModel).filter(ContentItemModel.id == content_id))
    content = result.scalars().first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    now = datetime.now(timezone.utc)
    approval = ApprovalModel(
        content_id=content_id,
        draft_hash=compute_draft_hash(content),
        status="rejected",
        approved_by=request.approved_by,
        decided_at=now
    )
    db.add(approval)
    
    content.status = "rejected"
    
    record_event(
        db, 
        agent_name=request.approved_by or "Human", 
        event_type="content_rejected", 
        message=f"Content rejected: {content.title}. Reason: {request.reason}",
        metadata={"content_id": content_id, "reason": request.reason}
    )
    
    await db.commit()
    return {"status": "rejected", "content_id": content_id}

@router.post("/content/{content_id}/publish")
async def trigger_publish(content_id: str, db: AsyncSession = Depends(get_db)):
    # 1. Load content item
    result = await db.execute(select(ContentItemModel).filter(ContentItemModel.id == content_id))
    content = result.scalars().first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    # 2. Find the latest approved approval for this content
    appr_result = await db.execute(
        select(ApprovalModel)
        .filter(ApprovalModel.content_id == content_id, ApprovalModel.status == "approved")
        .order_by(ApprovalModel.created_at.desc())
        .limit(1)
    )
    approval = appr_result.scalars().first()
    
    if not approval:
        raise HTTPException(status_code=400, detail="No valid approval found for this content")
    
    # 3. Enqueue the publish task
    # Note: .send is the Dramatiq way to enqueue a task
    publish_content.send(content.id, approval.id, approval.draft_hash)
    
    return {
        "status": "publish_enqueued",
        "content_id": content_id,
        "approval_id": approval.id
    }
