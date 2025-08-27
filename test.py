from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

try:
    client.server_info()  # forces a connection
    print("Connected successfully!")
except Exception as e:
    print("Connection failed:", e)
