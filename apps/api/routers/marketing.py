from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from datetime import datetime, timedelta
from apps.models.base import get_db
from apps.models.content_item import ContentItemModel
from apps.models.source import SourceModel
from apps.api.auth import require_viewer

router = APIRouter()

class MarketingActivityItem(BaseModel):
    """Marketing activity and evidence registry item."""
    id: str
    title: str
    agent: str
    objective: Optional[str]
    target_audience: Optional[str]
    source_id: Optional[str]
    format: Optional[str]
    channel: Optional[str]
    status: str
    created_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    approved_at: Optional[datetime]
    approver: Optional[str]
    published_at: Optional[datetime]
    post_url: Optional[str]
    post_id: Optional[str]
    publish_error: Optional[str]
    live_url: Optional[str]
    is_real_publish: bool

class MarketingActivityResponse(BaseModel):
    """Response containing marketing activity items."""
    items: List[MarketingActivityItem]
    total_count: int
    real_publish_count: int
    dry_run_count: int

@router.get("/marketing/activity", summary="Get Marketing Activity & Evidence Registry", description="Retrieve all marketing content with full lineage: created → approved → published → live URL")
async def get_marketing_activity(
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    only_real: bool = Query(False, description="Only show real (non-dry-run) publications"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_viewer)
):
    """
    Get marketing activity and evidence registry.
    
    Returns full lineage for each content item:
    - Created (agent, objective, created_at)
    - Approved (approver, approved_at/status)
    - Published (channel, published_at, live post_url, post_id)
    - Any publish_error/retry info
    - Linked source_id
    - Analytics/metrics if available
    """
    # Build base query
    query = select(ContentItemModel).order_by(desc(ContentItemModel.created_at))
    
    # Apply filters
    conditions = []
    
    if start_date:
        conditions.append(ContentItemModel.created_at >= start_date)
    
    if end_date:
        conditions.append(ContentItemModel.created_at <= end_date)
    
    if channel:
        conditions.append(ContentItemModel.channel == channel)
    
    if status:
        conditions.append(ContentItemModel.status == status)
    
    if only_real:
        # Only show real publications (has post_url and not dry-run indicators)
        conditions.append(
            and_(
                ContentItemModel.post_url.isnot(None),
                ContentItemModel.post_url != "",
                ~ContentItemModel.post_url.like("%dry-run%")
            )
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Execute query
    result = await db.execute(query)
    content_items = result.scalars().all()
    
    # Build response items
    items = []
    real_count = 0
    dry_run_count = 0
    
    for item in content_items:
        # Determine if this is a real publish
        is_real = (
            item.post_url is not None 
            and item.post_url != "" 
            and "dry-run" not in item.post_url.lower()
            and item.post_id is not None
            and item.post_id != ""
        )
        
        if is_real:
            real_count += 1
        else:
            dry_run_count += 1
        
        # Get source information if available
        source_info = None
        if item.source_id:
            source_result = await db.execute(
                select(SourceModel).where(SourceModel.id == item.source_id)
            )
            source = source_result.scalar_one_or_none()
            if source:
                source_info = {
                    "source_url": source.url,
                    "source_title": source.title,
                    "retrieval_date": source.retrieval_date
                }
        
        activity_item = MarketingActivityItem(
            id=item.id,
            title=item.title,
            agent=item.author_agent,
            objective=item.objective,
            target_audience=item.target_audience,
            source_id=item.source_id,
            format=item.format,
            channel=item.channel,
            status=item.status,
            created_at=item.created_at,
            scheduled_at=item.scheduled_at,
            approved_at=item.approved_at,
            approver=item.approver,
            published_at=item.published_at,
            post_url=item.post_url,
            post_id=item.post_id,
            publish_error=item.publish_error,
            live_url=item.post_url if is_real else None,
            is_real_publish=is_real
        )
        
        items.append(activity_item)
    
    return MarketingActivityResponse(
        items=items,
        total_count=len(items),
        real_publish_count=real_count,
        dry_run_count=dry_run_count
    )

@router.get("/marketing/activity/{content_id}", summary="Get specific marketing activity", description="Retrieve detailed information for a specific content item")
async def get_marketing_activity_detail(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_viewer)
):
    """Get detailed information for a specific content item."""
    result = await db.execute(
        select(ContentItemModel).where(ContentItemModel.id == content_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    # Determine if this is a real publish
    is_real = (
        item.post_url is not None 
        and item.post_url != "" 
        and "dry-run" not in item.post_url.lower()
        and item.post_id is not None
        and item.post_id != ""
    )
    
    # Get source information if available
    source_info = None
    if item.source_id:
        source_result = await db.execute(
            select(SourceModel).where(SourceModel.id == item.source_id)
        )
        source = source_result.scalar_one_or_none()
        if source:
            source_info = {
                "source_url": source.url,
                "source_title": source.title,
                "retrieval_date": source.retrieval_date,
                "publisher": source.publisher,
                "author": source.author
            }
    
    return {
        "id": item.id,
        "title": item.title,
        "body": item.body,
        "variants": item.variants,
        "agent": item.author_agent,
        "objective": item.objective,
        "target_audience": item.target_audience,
        "source_id": item.source_id,
        "source": source_info,
        "format": item.format,
        "channel": item.channel,
        "status": item.status,
        "created_at": item.created_at,
        "scheduled_at": item.scheduled_at,
        "approved_at": item.approved_at,
        "approver": item.approver,
        "published_at": item.published_at,
        "post_url": item.post_url,
        "post_id": item.post_id,
        "publish_error": item.publish_error,
        "live_url": item.post_url if is_real else None,
        "is_real_publish": is_real,
        "updated_at": item.updated_at
    }