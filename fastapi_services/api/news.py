from fastapi import APIRouter, HTTPException, Depends
from core.database import db
from typing import List, Dict, Any

router = APIRouter()

@router.get("/latest", response_model=List[Dict[str, Any]])
async def get_latest_news(limit: int = 20):
    """
    Fetch the most recently ingested news articles.
    """
    if db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    cursor = db.db.news_articles.find({}, {"_id": 0}).sort("published_at", -1).limit(limit)
    articles = await cursor.to_list(length=limit)
    
    # Attach quiz_id to each article if it has a generated quiz
    for article in articles:
        quiz = await db.db.quizzes.find_one({"article_id": article["article_id"]})
        article["quiz_id"] = quiz["quiz_id"] if quiz else None
        
    return articles

@router.get("/{article_id}", response_model=Dict[str, Any])
async def get_news_article(article_id: str):
    """
    Fetch a specific news article by ID.
    """
    if db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    article = await db.db.news_articles.find_one({"article_id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    # Attach quiz_id
    quiz = await db.db.quizzes.find_one({"article_id": article_id})
    article["quiz_id"] = quiz["quiz_id"] if quiz else None
        
    return article
