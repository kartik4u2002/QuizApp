from motor.motor_asyncio import AsyncIOMotorClient
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_to_database(self):
        logger.info("Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        # Parse DB name from URI safely, falling back to 'nlp_quiz_db'
        uri_path = settings.MONGO_URI.split("?")[0].rstrip("/")
        db_name = uri_path.split("/")[-1]
        if not db_name or "mongodb" in db_name or ":" in db_name or "@" in db_name or "." in db_name:
            db_name = "nlp_quiz_db"
        self.db = self.client[db_name]
        logger.info("Connected to MongoDB.")

    async def close_database_connection(self):
        logger.info("Closing MongoDB connection...")
        if self.client:
            self.client.close()
        logger.info("MongoDB connection closed.")

db = Database()
