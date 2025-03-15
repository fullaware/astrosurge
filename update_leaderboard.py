import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import find_elements  # Ensure find_elements is imported

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collection
db = mongodb_client["asteroids"]  # Replace with your actual database name
leaderboard_collection = db["leaderboard"]

def update_leaderboard(uid: str, elements: list, total_mined_mass: int):
    """
    This function updates the leaderboard with the mined elements by use.
    """
    try:
        # Find elements by use
        elements_by_use = find_elements.find_elements(elements, total_mined_mass)
        
        # Update the leaderboard
        for element in elements_by_use:
            leaderboard_collection.update_one(
                {"uid": uid},
                {"$inc": {f"uses.{element['use']}.mass_kg": element["total_mass_kg"]}},
                upsert=True
            )
        logging.info(f"Leaderboard updated for uid: {uid}")
    except Exception as e:
        logging.error(f"Error updating leaderboard: {e}")

if __name__ == "__main__":
    uid = "Brandon"
    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]
    total_mined_mass = 250
    update_leaderboard(uid, sample_elements, total_mined_mass)