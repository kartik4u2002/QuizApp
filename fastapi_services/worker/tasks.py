import asyncio
import uuid
import datetime
from celery.utils.log import get_task_logger
from worker.celery_app import celery_app
from services.news_fetcher import fetch_all_news
from ml_models.nlp_pipeline import nlp_pipeline
from ml_models.quiz_engine import quiz_engine
import pymongo
import os

logger = get_task_logger(__name__)

# Synchronous MongoDB connection for Celery (since Celery is synchronous)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/nlp_quiz_db")
try:
    client = pymongo.MongoClient(MONGO_URI)
    # Parse DB name from URI safely, falling back to 'nlp_quiz_db'
    uri_path = MONGO_URI.split("?")[0].rstrip("/")
    db_name = uri_path.split("/")[-1]
    if not db_name or "mongodb" in db_name or ":" in db_name or "@" in db_name or "." in db_name:
        db_name = "nlp_quiz_db"
    db = client[db_name]
except Exception as e:
    logger.error(f"Failed to connect to MongoDB in Celery: {e}")
    db = None

@celery_app.task(name="worker.tasks.fetch_and_process_news")
def fetch_and_process_news():
    """
    Periodic task to fetch news and trigger processing.
    Since fetch_all_news is async, we need an event loop to run it.
    """
    logger.info("Starting scheduled news fetch...")
    
    loop = asyncio.get_event_loop()
    articles = loop.run_until_complete(fetch_all_news())
    
    if not articles:
        logger.info("No new articles fetched.")
        return
        
    for article in articles:
        # Check if URL already exists in MongoDB
        if db is not None:
            exists = db.news_articles.find_one({"url": article["url"]})
            if exists:
                continue # Skip duplicates
                
        # Insert raw article
        article_id = str(uuid.uuid4())
        article_doc = {
            "article_id": article_id,
            "title": article["title"],
            "content": article["content"],
            "url": article["url"],
            "source": article["source"],
            "published_at": article["published_at"],
            "status": "pending",
            "created_at": datetime.datetime.utcnow()
        }
        
        if db is not None:
            db.news_articles.insert_one(article_doc)
            
        # Trigger NLP processing asynchronously as another celery task
        process_article.delay(article_id)

@celery_app.task(name="worker.tasks.process_article")
def process_article(article_id: str):
    """
    Processes an article to generate a quiz.
    """
    logger.info(f"Processing article: {article_id}")
    
    if db is None:
        logger.error("No DB connection.")
        return
        
    article = db.news_articles.find_one({"article_id": article_id})
    if not article:
        logger.error(f"Article not found: {article_id}")
        return
        
    try:
        # 1. NLP Pipeline (Clean, Sentence Tokenize, NER)
        processed_data = nlp_pipeline.process_article(article["content"])
        
        # 2. Quiz Generation
        quiz_items = quiz_engine.create_quiz_from_article(processed_data)
        
        if not quiz_items:
            logger.warning(f"No quiz generated for article {article_id}")
            db.news_articles.update_one({"article_id": article_id}, {"$set": {"status": "processed_no_quiz"}})
            return
            
        # 3. Save Quiz to DB
        quiz_id = str(uuid.uuid4())
        quiz_doc = {
            "quiz_id": quiz_id,
            "article_id": article_id,
            "topic": article.get("title", "General News"), # In a real app, use zero-shot classification for topic
            "difficulty": "medium",
            "questions": quiz_items,
            "created_at": datetime.datetime.utcnow()
        }
        
        db.quizzes.insert_one(quiz_doc)
        db.news_articles.update_one({"article_id": article_id}, {"$set": {"status": "processed"}})
        logger.info(f"Quiz successfully generated for article: {article_id}")
        
    except Exception as e:
        logger.error(f"Error processing article {article_id}: {e}")
        db.news_articles.update_one({"article_id": article_id}, {"$set": {"status": "failed"}})
