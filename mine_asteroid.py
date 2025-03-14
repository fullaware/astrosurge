"""
Description:
This script simulates extracting material from an asteroid over 1 hour, examines the contents of that material for known elements, and measures how much mass of each element has been extracted. Upon completion, the function updates the asteroid document with the updated elements and mined_mass_kg fields. Returns the updated asteroid document and a list of elements mined.

The script also includes functions to:
- Retrieve an asteroid document from MongoDB by its full name.
- Update the asteroid document in MongoDB with the updated elements and mass fields.

Functions:
- log(message, level=logging.INFO): Logs messages with a specified logging level.
- get_asteroid_by_name(asteroid_name: str) -> dict: Retrieves an asteroid document from MongoDB by its full name.
- mine_asteroid(asteroid: dict, extraction_rate: int, uid: str) -> (dict, list): Simulates extracting material from an asteroid, examines the contents for known elements, and measures the mass of each element extracted. Updates the asteroid document with the new elements and mined mass.
- update_asteroid(asteroid: dict): Updates the asteroid document in MongoDB with the updated elements and mass fields.

Usage:
- The script can be run as a standalone module to simulate mining an asteroid and updating its document in MongoDB.
- Logging can be configured to output to the console or a file.
"""

import os
import random
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from the environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collections
db = mongodb_client["asteroids"]  # Replace with your actual database name
asteroids_collection = db["asteroids"]
mined_asteroids_collection = db["mined_asteroids"]

# Global logging variable
LOGGING = True
LOG_TO_FILE = False  # Set logging to file as optional and False by default

# Configure logging
log_filename = f"beryl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
handlers = [logging.StreamHandler()]
if LOG_TO_FILE:
    handlers.append(logging.FileHandler(log_filename))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=handlers)

def log(message, level=logging.INFO):
    if LOGGING:
        logging.log(level, message)

def get_asteroid_by_name(asteroid_name: str) -> dict:
    """
    This function retrieves an asteroid document from the mined_asteroids collection first.
    If not found, it retrieves from the asteroids collection.
    """
    asteroid = mined_asteroids_collection.find_one({"full_name": asteroid_name}, {"_id": 0})
    if not asteroid:
        asteroid = asteroids_collection.find_one({"full_name": asteroid_name}, {"_id": 0})
    return asteroid

def mine_asteroid(asteroid, extraction_rate, uid):
    """
    This function simulates mining an asteroid.
    """
    mined_mass = 0
    total_elements_mined = []
    extraction_rate = random.randint(1,extraction_rate)  # Maximum extraction rate

    for element in asteroid['elements']:
        remaining_mass_to_mine = extraction_rate - mined_mass
        if remaining_mass_to_mine <= 0:
            break

        # Ensure the range for randint is valid
        max_mineable_mass = min(remaining_mass_to_mine, element["mass_kg"])
        if max_mineable_mass < 1:
            max_mineable_mass = 1

        actual_mined_mass = random.randint(1, max_mineable_mass)  # Ensure actual_mined_mass is less than or equal to max_mineable_mass
        element["mass_kg"] -= actual_mined_mass
        mined_mass += actual_mined_mass
        total_elements_mined.append({"name": element["name"], "mined_mass_kg": actual_mined_mass})

        logging.info(f"Removed {actual_mined_mass} kg from {element['name']}.")

    asteroid['mass'] -= mined_mass
    asteroid['mined_elements_kg'] = mined_mass
    asteroid['uid'] = uid

    return asteroid, total_elements_mined

def update_asteroid(asteroid: dict):
    """
    This function updates the asteroid document in MongoDB with the updated elements and mass fields.
    """
    if "uid" not in asteroid:
        raise ValueError("Asteroid document must contain a 'uid' field.")

    mined_asteroids_collection.update_one(
        {"full_name": asteroid["full_name"]},
        {"$set": asteroid},
        upsert=True
    )

if __name__ == "__main__":
    asteroid_name = "1 Ceres"
    log(f"Retrieving asteroid info for {asteroid_name}", logging.INFO)

    asteroid = get_asteroid_by_name(asteroid_name)
    log(f"Asteroid mass before mining: {asteroid['mass']} kg", logging.INFO)

    # Write the asteroid object to the mined_asteroids collection before mining
    mined_asteroids_collection.insert_one(asteroid)

    extraction_rate = 1000  # Set the maximum extraction rate
    log(f"Mining asteroid...{asteroid_name}", logging.INFO)
    asteroid, total_elements_mined = mine_asteroid(asteroid, extraction_rate, uid)
    log(f"Total elements mined: {sum([element['mined_mass_kg'] for element in total_elements_mined])} kg", logging.INFO)
    log(f"Asteroid mass after mining: {asteroid['mass']} kg", logging.INFO)

    # Update the asteroid in the mined_asteroids collection
    update_asteroid(asteroid)