from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from core.database import db
from worker.tasks import process_article
from typing import List, Dict, Any
import datetime

router = APIRouter()

class GenerateQuizRequest(BaseModel):
    article_id: str

@router.get("/latest", response_model=List[Dict[str, Any]])
async def get_latest_quizzes(limit: int = 10):
    """
    Fetch the most recently generated quizzes.
    """
    if db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    cursor = db.db.quizzes.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    quizzes = await cursor.to_list(length=limit)
    return quizzes

@router.get("/topic/{topic}", response_model=List[Dict[str, Any]])
async def get_quizzes_by_topic(topic: str, limit: int = 10):
    """
    Fetch quizzes filtered by topic.
    """
    if db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    cursor = db.db.quizzes.find(
        {"topic": {"$regex": topic, "$options": "i"}}, 
        {"_id": 0}
    ).sort("created_at", -1).limit(limit)
    
    quizzes = await cursor.to_list(length=limit)
    return quizzes

@router.post("/generate", response_model=Dict[str, str])
async def manual_generate_quiz(request: GenerateQuizRequest):
    """
    Manually trigger quiz generation for a specific article.
    """
    if db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    article = await db.db.news_articles.find_one({"article_id": request.article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    # Trigger celery task asynchronously
    process_article.delay(request.article_id)
    
    return {"message": "Quiz generation started in the background."}
