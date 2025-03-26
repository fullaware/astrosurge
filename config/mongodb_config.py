from pymongo import MongoClient
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
ships_collection = db["ships"]  # Ensure this line is present

# Add any other collections as needed
elements_collection = db["elements"]
asteroids_collection = db["asteroids"]
mined_asteroids_collection = db["mined_asteroids"]
missions_collection = db["missions"]