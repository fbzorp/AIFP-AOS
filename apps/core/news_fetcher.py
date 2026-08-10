"""
Minimal news/web search fetcher for real-time source retrieval.
Supports credential-gated API integrations for news and web search.
"""

import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from apps.api.config import settings

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches real news sources from configurable APIs."""
    
    def __init__(self):
        self.news_api_key = getattr(settings, "NEWS_API_KEY", None)
        self.serper_api_key = getattr(settings, "SERPER_API_KEY", None)
    
    async def fetch_news_api(self, query: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch news from NewsAPI.org (requires NEWS_API_KEY in .env).
        
        Args:
            query: Search query
            page_size: Number of results to fetch
        
        Returns:
            List of articles with url, title, content, author, published_date
        """
        if not self.news_api_key:
            logger.warning("NEWS_API_KEY not configured, skipping NewsAPI fetch")
            return []
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": self.news_api_key,
            "pageSize": page_size,
            "sortBy": "publishedAt",
            "language": "en"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"NewsAPI request failed: {response.status}")
                        return []
                    
                    data = await response.json()
                    articles = []
                    
                    for article in data.get("articles", []):
                        articles.append({
                            "url": article.get("url"),
                            "title": article.get("title"),
                            "content": article.get("description") or article.get("content", ""),
                            "author": article.get("author"),
                            "published_date": article.get("publishedAt"),
                            "source": article.get("source", {}).get("name")
                        })
                    
                    logger.info(f"Fetched {len(articles)} articles from NewsAPI")
                    return articles
                    
        except Exception as e:
            logger.error(f"NewsAPI fetch error: {e}")
            return []
    
    async def fetch_serper_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch web search results from Serper.dev (requires SERPER_API_KEY in .env).
        
        Args:
            query: Search query
            num_results: Number of results to fetch
        
        Returns:
            List of search results with url, title, snippet
        """
        if not self.serper_api_key:
            logger.warning("SERPER_API_KEY not configured, skipping Serper fetch")
            return []
        
        url = "https://google.serper.dev/search"
        params = {
            "q": query,
            "apiKey": self.serper_api_key,
            "num": num_results
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as response:
                    if response.status != 200:
                        logger.error(f"Serper request failed: {response.status}")
                        return []
                    
                    data = await response.json()
                    results = []
                    
                    for item in data.get("organic", []):
                        results.append({
                            "url": item.get("link"),
                            "title": item.get("title"),
                            "content": item.get("snippet"),
                            "author": None,
                            "published_date": None,
                            "source": "web_search"
                        })
                    
                    logger.info(f"Fetched {len(results)} results from Serper")
                    return results
                    
        except Exception as e:
            logger.error(f"Serper fetch error: {e}")
            return []
    
    async def fetch_real_sources(self, query: str) -> List[Dict[str, Any]]:
        """
        Fetch real sources from available APIs.
        Tries multiple sources and returns combined results.
        
        Args:
            query: Search query for sources
        
        Returns:
            List of real sources with metadata
        """
        all_sources = []
        
        # Try NewsAPI first
        news_sources = await self.fetch_news_api(query)
        all_sources.extend(news_sources)
        
        # Try Serper as fallback
        if len(all_sources) < 5:
            web_sources = await self.fetch_serper_search(query)
            all_sources.extend(web_sources)
        
        return all_sources


# Singleton instance
news_fetcher = NewsFetcher()
