"""
Google Search Console API client for fetching real analytics data.
Requires GOOGLE_SEARCH_CONSOLE_JSON_KEY env var with service account credentials.
"""

import logging
import json
from typing import Dict, Any, Optional
from apps.api.config import settings

logger = logging.getLogger(__name__)


class GoogleSearchConsoleClient:
    """Client for Google Search Console API to fetch real search analytics."""
    
    def __init__(self):
        self._configured = False
        self._credentials = None
        self._service = None
        self._check_configuration()
    
    def _check_configuration(self):
        """Check if Google Search Console credentials are configured."""
        # Check for service account JSON key
        json_key = getattr(settings, "GOOGLE_SEARCH_CONSOLE_JSON_KEY", None)
        if json_key:
            try:
                # Parse the JSON key
                credentials_dict = json.loads(json_key)
                self._credentials = credentials_dict
                self._configured = True
                logger.info("Google Search Console client configured with service account")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GOOGLE_SEARCH_CONSOLE_JSON_KEY: {e}")
                self._configured = False
        else:
            logger.info("Google Search Console client not configured (no credentials)")
    
    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return self._configured
    
    def _initialize_service(self):
        """Initialize the Google Search Console API service."""
        if not self._configured or self._service is not None:
            return
        
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            # Create credentials from the JSON key
            credentials = Credentials.from_service_account_info(
                self._credentials,
                scopes=['https://www.googleapis.com/auth/webmasters.readonly']
            )
            
            # Build the Search Console API service
            self._service = build('searchconsole', 'v1', credentials=credentials)
            logger.info("Google Search Console API service initialized")
            
        except ImportError as e:
            logger.error(f"Failed to import Google libraries: {e}")
            self._configured = False
        except Exception as e:
            logger.error(f"Failed to initialize Search Console service: {e}")
            self._configured = False
    
    async def fetch_search_analytics(
        self,
        url: str,
        start_date: str,
        end_date: str,
        dimensions: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Fetch search analytics data from Google Search Console.
        
        Args:
            url: The URL pattern to query (e.g., "https://example.com/*")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dimensions: List of dimensions (e.g., ["date", "query"])
        
        Returns:
            Dict with analytics data or error message
        """
        if not self._configured:
            return {
                "available": False,
                "data_source": "Google Search Console",
                "message": "unavailable/not configured",
                "error": "GOOGLE_SEARCH_CONSOLE_JSON_KEY not set"
            }
        
        try:
            self._initialize_service()
            
            if not self._service:
                return {
                    "available": False,
                    "data_source": "Google Search Console",
                    "message": "service initialization failed",
                    "error": "Failed to initialize Search Console service"
                }
            
            # Prepare the request body
            request_body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions or ['date'],
                'rowLimit': 1000
            }
            
            # Execute the query
            response = self._service.searchanalytics().query(
                siteUrl=url,
                body=request_body
            ).execute()
            
            # Extract data from response
            rows = response.get('rows', [])
            total_impressions = sum(row.get('impressions', 0) for row in rows)
            total_clicks = sum(row.get('clicks', 0) for row in rows)
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            avg_position = sum(row.get('position', 0) for row in rows) / len(rows) if rows else 0
            
            logger.info(f"Successfully fetched Search Console data for {url}: {total_impressions} impressions, {total_clicks} clicks")
            
            return {
                "available": True,
                "data_source": "Google Search Console",
                "impressions": total_impressions,
                "clicks": total_clicks,
                "ctr": round(avg_ctr, 2),
                "avg_position": round(avg_position, 2),
                "rows": rows,
                "message": "successfully fetched data"
            }
            
        except Exception as e:
            logger.error(f"Error fetching Google Search Console data: {e}")
            return {
                "available": False,
                "data_source": "Google Search Console",
                "message": "error fetching data",
                "error": str(e)
            }
    
    async def get_site_metrics(self, url: str) -> Dict[str, Any]:
        """
        Get key metrics for a specific site URL.
        
        Args:
            url: The site URL to query
        
        Returns:
            Dict with impressions, clicks, CTR, position data
        """
        if not self._configured:
            return {
                "available": False,
                "data_source": "Google Search Console",
                "message": "unavailable/not configured",
                "error": "GOOGLE_SEARCH_CONSOLE_JSON_KEY not set"
            }
        
        try:
            # Use fetch_search_analytics with default date range (last 28 days)
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
            
            return await self.fetch_search_analytics(
                url=url,
                start_date=start_date,
                end_date=end_date,
                dimensions=['date']
            )
            
        except Exception as e:
            logger.error(f"Error getting site metrics: {e}")
            return {
                "available": False,
                "data_source": "Google Search Console",
                "message": "error fetching data",
                "error": str(e)
            }