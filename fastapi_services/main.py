from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from core.database import db
from api import news, quiz
import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to DB
    await db.connect_to_database()
    yield
    # Shutdown: close DB connection
    await db.close_database_connection()

app = FastAPI(title="NLP Quiz API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news.router, prefix="/api/v1/news", tags=["News"])
app.include_router(quiz.router, prefix="/api/v1/quizzes", tags=["Quiz"])

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}
