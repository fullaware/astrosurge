from pymongo import MongoClient
from bson import Int64
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collections
db = mongodb_client["asteroids"]  # Replace with your actual database name
users_collection = db["users"]
elements_collection = db["elements"]
asteroids_collection = db["asteroids"]
mined_asteroids_collection = db["mined_asteroids"]