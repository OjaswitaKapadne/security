import pymongo
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")

try:
    client = pymongo.MongoClient(
        MONGO_DB_URL,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )

    client.admin.command('ping')
    print("✅ MongoDB Connected Successfully!")

except Exception as e:
    print("❌ Connection Failed:")
    print(e)