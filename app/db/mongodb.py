from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings 

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_connection = Database()

async def connect_to_mongo():
    # FIXED: Accessing property directly, no parentheses or arguments
    db_connection.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_connection.db = db_connection.client[settings.DATABASE_NAME]

async def close_mongo_connection():
    if db_connection.client:
        db_connection.client.close()

def get_db():
    return db_connection.db