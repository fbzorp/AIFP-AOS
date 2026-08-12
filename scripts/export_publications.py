#!/usr/bin/env python3
"""
Export Marketing Publications to CSV

This script queries the database for real (non-dry-run) publications
within a date range and exports them to CSV format.

Usage:
    python scripts/export_publications.py [days]
    
    days: Number of days to look back (default: 7 for this week)
"""

import sys
import csv
import argparse
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from apps.models.base import Base
from apps.models.content_item import ContentItemModel
from apps.models.source import SourceModel
from apps.api.config import settings


def export_publications(days: int = 7, output_file: str = None):
    """
    Export real publications to CSV.
    
    Args:
        days: Number of days to look back
        output_file: Output CSV file path (default: publications_{date}.csv)
    """
    # Create database connection
    # Use synchronous engine for the export script
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")
    elif db_url.startswith("sqlite+aiosqlite"):
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite")
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Calculate date range
        cutoff = datetime.now() - timedelta(days=days)
        
        # Query for real publications (non-dry-run)
        query = select(ContentItemModel).where(
            and_(
                ContentItemModel.status == "published",
                ContentItemModel.post_url.isnot(None),
                ContentItemModel.post_url != "",
                ~ContentItemModel.post_url.like("%dry-run%"),
                ContentItemModel.published_at >= cutoff
            )
        ).order_by(desc(ContentItemModel.published_at))
        
        result = session.execute(query)
        content_items = result.scalars().all()
        
        if not content_items:
            print(f"No real publications found in the last {days} days.")
            return
        
        # Generate output filename if not provided
        if not output_file:
            output_file = f"publications_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Prepare CSV data
        csv_data = []
        for item in content_items:
            # Get source information if available
            source_info = ""
            if item.source_id:
                source_result = session.execute(
                    select(SourceModel).where(SourceModel.id == item.source_id)
                )
                source = source_result.scalar_one_or_none()
                if source:
                    source_info = source.url or ""
            
            csv_data.append({
                "date": item.published_at.strftime("%Y-%m-%d %H:%M:%S") if item.published_at else "",
                "agent": item.author_agent or "",
                "channel": item.channel or "",
                "objective": item.objective or "",
                "title": item.title or "",
                "live_url": item.post_url or "",
                "post_id": item.post_id or "",
                "source_id": item.source_id or "",
                "source_url": source_info,
                "format": item.format or "",
                "target_audience": item.target_audience or ""
            })
        
        # Write CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["date", "agent", "channel", "objective", "title", "live_url", 
                         "post_id", "source_id", "source_url", "format", "target_audience"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"Exported {len(csv_data)} real publications to {output_file}")
        print(f"Date range: {cutoff.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        
        # Print summary
        print("\nSummary:")
        channel_counts = {}
        for item in csv_data:
            channel = item["channel"] or "unknown"
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        for channel, count in sorted(channel_counts.items()):
            print(f"  {channel}: {count}")
        
    except Exception as e:
        print(f"Error exporting publications: {e}")
        sys.exit(1)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Export marketing publications to CSV"
    )
    parser.add_argument(
        "days",
        nargs="?",
        type=int,
        default=7,
        help="Number of days to look back (default: 7 for this week)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: publications_{date}.csv)"
    )
    
    args = parser.parse_args()
    
    print(f"Exporting publications from the last {args.days} days...")
    export_publications(days=args.days, output_file=args.output)


if __name__ == "__main__":
    main()