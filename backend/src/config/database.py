"""
Database configuration and connection management
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
database_name = os.environ['DB_NAME']

# Create database client and connection
client = AsyncIOMotorClient(mongo_url)
db = client[database_name]

async def get_database():
    """Get database instance"""
    return db

async def close_database_connection():
    """Close database connection"""
    client.close()

# Collections
COLLECTIONS = {
    'tenants': 'tenants',
    'products': 'products',
    'orders': 'orders',
    'return_requests': 'return_requests',
    'return_rules': 'return_rules'
}