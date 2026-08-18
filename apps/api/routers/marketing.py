from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from datetime import datetime, timedelta
import csv
import io
from apps.models.base import get_db
from apps.models.content_item import ContentItemModel
from apps.models.source import SourceModel
from apps.api.auth import require_viewer

router = APIRouter()

class MarketingActivityItem(BaseModel):
    """Marketing activity and evidence registry item with full SEO and analytics metadata."""
    id: str
    title: str
    agent: str
    objective: Optional[str]
    target_audience: Optional[str]
    source_id: Optional[str]
    source_urls: Optional[list]  # List of source URLs
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
    
    # SEO Metadata
    target_keyword: Optional[str]
    search_intent: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    canonical_url: Optional[str]
    indexing_status: Optional[str]
    internal_links: Optional[list]
    
    # Analytics Metrics
    impressions: Optional[int]
    clicks: Optional[int]
    engagement: Optional[int]
    referrals: Optional[int]
    conversions: Optional[int]
    last_analytics_update: Optional[datetime]

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
            source_urls=item.source_urls,
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
            is_real_publish=is_real,
            # SEO Metadata
            target_keyword=item.target_keyword,
            search_intent=item.search_intent,
            meta_title=item.meta_title,
            meta_description=item.meta_description,
            canonical_url=item.canonical_url,
            indexing_status=item.indexing_status,
            internal_links=item.internal_links,
            # Analytics Metrics
            impressions=item.impressions,
            clicks=item.clicks,
            engagement=item.engagement,
            referrals=item.referrals,
            conversions=item.conversions,
            last_analytics_update=item.last_analytics_update
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
        "source_urls": item.source_urls,
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
        "updated_at": item.updated_at,
        # SEO Metadata
        "target_keyword": item.target_keyword,
        "search_intent": item.search_intent,
        "meta_title": item.meta_title,
        "meta_description": item.meta_description,
        "canonical_url": item.canonical_url,
        "indexing_status": item.indexing_status,
        "internal_links": item.internal_links,
        # Analytics Metrics
        "impressions": item.impressions,
        "clicks": item.clicks,
        "engagement": item.engagement,
        "referrals": item.referrals,
        "conversions": item.conversions,
        "last_analytics_update": item.last_analytics_update
    }

@router.get("/marketing/activity/export/csv", summary="Export Marketing Activity to CSV", description="Export full marketing activity registry to CSV format")
async def export_marketing_activity_csv(
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    only_real: bool = Query(False, description="Only include real (non-dry-run) publications"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_viewer)
):
    """Export marketing activity registry to CSV format."""
    # Build base query (same as get_marketing_activity)
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
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = [
        "ID", "Title", "Agent", "Channel", "Status", "Created At", "Published At",
        "Post URL", "Post ID", "Live URL", "Is Real Publish",
        "Target Keyword", "Search Intent", "Meta Title", "Meta Description",
        "Canonical URL", "Indexing Status", "Impressions", "Clicks",
        "Engagement", "Referrals", "Conversions", "Last Analytics Update"
    ]
    writer.writerow(header)
    
    # Write rows
    for item in content_items:
        is_real = (
            item.post_url is not None 
            and item.post_url != "" 
            and "dry-run" not in item.post_url.lower()
            and item.post_id is not None
            and item.post_id != ""
        )
        
        row = [
            item.id,
            item.title,
            item.author_agent,
            item.channel,
            item.status,
            item.created_at.isoformat() if item.created_at else "",
            item.published_at.isoformat() if item.published_at else "",
            item.post_url or "",
            item.post_id or "",
            item.post_url if is_real else "",
            "Yes" if is_real else "No",
            item.target_keyword or "",
            item.search_intent or "",
            item.meta_title or "",
            item.meta_description or "",
            item.canonical_url or "",
            item.indexing_status or "",
            item.impressions or 0,
            item.clicks or 0,
            item.engagement or 0,
            item.referrals or 0,
            item.conversions or 0,
            item.last_analytics_update.isoformat() if item.last_analytics_update else ""
        ]
        writer.writerow(row)
    
    # Reset buffer position
    output.seek(0)
    
    # Return CSV as streaming response
    csv_content = output.getvalue()
    csv_bytes = csv_content.encode('utf-8')
    
    def generate():
        yield csv_bytes
    
    return StreamingResponse(
        generate(),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="marketing_activity_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv"'
        }
    )