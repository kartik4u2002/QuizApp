import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from core.config import settings

logger = logging.getLogger(__name__)

async def fetch_newsapi_articles() -> List[Dict[str, Any]]:
    """Fetch recent articles from NewsAPI for the last 24 hours."""
    if not settings.NEWSAPI_KEY:
        logger.warning("No NEWSAPI_KEY provided, skipping NewsAPI fetch.")
        return []
        
    from_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "news OR world OR general",
        "language": "en",
        "from": from_date,
        "sortBy": "publishedAt",
        "apiKey": settings.NEWSAPI_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get('articles', []):
                # We need content to generate a quiz
                if item.get('content') or item.get('description'):
                    articles.append({
                        "title": item.get('title'),
                        "content": item.get('content') or item.get('description'),
                        "url": item.get('url'),
                        "source": "NewsAPI",
                        "published_at": item.get('publishedAt')
                    })
            return articles
    except Exception as e:
        logger.error(f"Error fetching from NewsAPI: {e}")
        return []

async def fetch_gnews_articles() -> List[Dict[str, Any]]:
    """Fetch recent articles from GNews API for the last 24 hours."""
    if not settings.GNEWS_API_KEY:
        logger.warning("No GNEWS_API_KEY provided, skipping GNews fetch.")
        return []
        
    from_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://gnews.io/api/v4/top-headlines"
    params = {
        "lang": "en",
        "from": from_date,
        "token": settings.GNEWS_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get('articles', []):
                if item.get('content'):
                    articles.append({
                        "title": item.get('title'),
                        "content": item.get('content'),
                        "url": item.get('url'),
                        "source": "GNews",
                        "published_at": item.get('publishedAt')
                    })
            return articles
    except Exception as e:
        logger.error(f"Error fetching from GNews: {e}")
        return []

async def fetch_all_news() -> List[Dict[str, Any]]:
    """Fetch news from all configured sources."""
    newsapi = await fetch_newsapi_articles()
    gnews = await fetch_gnews_articles()
    
    # Combine and deduplicate based on URL
    all_articles = newsapi + gnews
    unique_articles = {article['url']: article for article in all_articles}.values()
    
    return list(unique_articles)
