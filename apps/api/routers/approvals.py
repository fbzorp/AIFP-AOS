from typing import List, Optional, Any, Dict
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apps.models.base import get_db
from apps.models.content_item import ContentItemModel
from apps.models.approval import ApprovalModel
from apps.models.audit_event import AuditEventModel
from apps.models.engagement_proposal import EngagementProposalModel
from apps.core.policy.engine import compute_draft_hash
from apps.core.audit.service import record_event
from apps.workers.tasks import publish_content
from sqlalchemy import or_

router = APIRouter()

class ApprovalDecisionRequest(BaseModel):
    approved_by: str
    expires_in_hours: Optional[int] = 24
    reason: Optional[str] = None

class ContentEditRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    variants: Optional[List[Dict[str, Any]]] = None

@router.get("/approvals")
async def list_approvals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApprovalModel).order_by(ApprovalModel.created_at.desc()).limit(50))
    return result.scalars().all()

@router.get("/content")
async def list_content_queue(db: AsyncSession = Depends(get_db)):
    """Returns content items ordered by status and creation date for the queue."""
    # Prioritize pending_review and draft statuses
    result = await db.execute(
        select(ContentItemModel)
        .order_by(
            desc(ContentItemModel.status == "pending_review"),
            desc(ContentItemModel.status == "draft"),
            ContentItemModel.created_at.desc()
        )
        .limit(50)
    )
    return result.scalars().all()

@router.patch("/content/{content_id}")
async def edit_content(content_id: str, request: ContentEditRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentItemModel).filter(ContentItemModel.id == content_id))
    content = result.scalars().first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    if request.title is not None:
        content.title = request.title
    if request.body is not None:
        content.body = request.body
    if request.variants is not None:
        content.variants = request.variants
        
    content.status = "draft" # Reset to draft after edit
    
    record_event(
        db, 
        agent_name="Human", 
        event_type="content_edited", 
        message=f"Content edited: {content.title}",
        metadata={"content_id": content_id}
    )
    
    await db.commit()
    return content

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
    publish_content.send(content.id, approval.id, approval.draft_hash)
    
    return {
        "status": "publish_enqueued",
        "content_id": content_id,
        "approval_id": approval.id
    }

# Days 10-11: Engagement Proposals & Calendar

@router.get("/engagement/proposals")
async def list_proposals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EngagementProposalModel)
        .order_by(EngagementProposalModel.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()

@router.post("/engagement/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EngagementProposalModel).filter(EngagementProposalModel.id == proposal_id))
    proposal = result.scalars().first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal.status = "approved"
    record_event(db, "Human", "engagement_approved", f"Approved proposal {proposal_id}", {"proposal_id": proposal_id})
    await db.commit()
    return {"status": "approved", "proposal_id": proposal_id}

@router.post("/engagement/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EngagementProposalModel).filter(EngagementProposalModel.id == proposal_id))
    proposal = result.scalars().first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal.status = "rejected"
    record_event(db, "Human", "engagement_rejected", f"Rejected proposal {proposal_id}", {"proposal_id": proposal_id})
    await db.commit()
    return {"status": "rejected", "proposal_id": proposal_id}

@router.get("/calendar")
async def get_calendar(db: AsyncSession = Depends(get_db)):
    """Returns content items that are scheduled or published."""
    result = await db.execute(
        select(ContentItemModel)
        .filter(
            or_(
                ContentItemModel.scheduled_at.isnot(None),
                ContentItemModel.published_at.isnot(None),
                ContentItemModel.status == "published"
            )
        )
        .order_by(ContentItemModel.published_at.desc(), ContentItemModel.scheduled_at.desc())
        .limit(100)
    )
    return result.scalars().all()
