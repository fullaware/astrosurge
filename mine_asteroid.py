import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint
from colorama import Fore, Style

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from the environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collection
db = mongodb_client["asteroids"]  # Replace with your actual database name
asteroids_collection = db["asteroids"]

def get_asteroid_by_name(asteroid_name: str) -> dict:
    """
    This function retrieves an asteroid document from MongoDB by its full name.
    If the class is missing, it assigns a random class, updates the asteroid, and runs the aggregation again.
    """
    return asteroids_collection.find({"full_name": asteroid_name}, {"_id": 0})

print(Fore.GREEN + "Retrieving asteroid by name..." + Style.RESET_ALL)
asteroid_name = "1 Ceres"
asteroid = get_asteroid_by_name(asteroid_name)
pprint(list(asteroid))