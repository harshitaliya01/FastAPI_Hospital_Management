from motor.motor_asyncio import AsyncIOMotorClient
import os

try:
    client = AsyncIOMotorClient(os.getenv("DB_URI"))
    db = client["hospital"]
except Exception as e:
    print(f"❌ Error connecting: {e}")