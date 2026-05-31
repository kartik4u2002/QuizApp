from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://mongodb:27017/nlp_quiz_db"
    REDIS_URL: str = "redis://redis:6379/0"
    
    NEWSAPI_KEY: Optional[str] = None
    GNEWS_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
