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

# Specify the database and collection
db = mongodb_client["asteroids"]  # Replace with your actual database name
asteroids_collection = db["asteroids"]

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
    This function retrieves an asteroid document from MongoDB by its full name.
    """
    return asteroids_collection.find_one({"full_name": asteroid_name}, {"_id": 0})

def mine_asteroid(asteroid: dict, extraction_rate: int) -> (dict, list):
    """
    This function simulates extracting material from an asteroid over 1 hour, 
    examining the contents of that material
    measure how much mass of each element has been extracted.

    Upon completion, the function updates the asteroid document with the updated elements and mined_mass_kg fields.

    Note: 

    """
    total_elements_mined = []
    mined_mass = random.randint(1, extraction_rate)
    remaining_mass_to_mine = mined_mass

    if "elements" in asteroid and asteroid["elements"]:
        while remaining_mass_to_mine > 0 and asteroid["elements"]:
            element = random.choice(asteroid["elements"])
            actual_mined_mass = random.randint(1, min(remaining_mass_to_mine, element["mass_kg"], mined_mass // 10))  # Ensure actual_mined_mass is less than 10% of mined_mass

            if element["mass_kg"] >= actual_mined_mass:
                element["mass_kg"] -= actual_mined_mass
                asteroid["mass"] -= actual_mined_mass
                remaining_mass_to_mine -= actual_mined_mass

                total_elements_mined.append({
                    "name": element["name"],
                    "number": element["number"],
                    "mined_mass_kg": actual_mined_mass
                })

                log(f"Removed {actual_mined_mass} kg from {element['name']}.", logging.INFO)
            else:
                log(f"Not enough mass in {element['name']} to remove {actual_mined_mass} kg.", logging.WARNING)
                asteroid["elements"].remove(element)
    else:
        log("No elements found in the asteroid.", logging.WARNING)

    return asteroid, total_elements_mined

def update_asteroid(asteroid: dict):
    """
    This function updates the asteroid document in MongoDB with the updated elements and mass fields.
    """
    asteroids_collection.update_one(
        {"full_name": asteroid["full_name"]},
        {"$set": {"elements": asteroid["elements"], "mass": asteroid["mass"]}}
    )

if __name__ == "__main__":
    asteroid_name = "1 Ceres"
    log(f"Retrieving asteroid info for {asteroid_name}", logging.INFO)

    asteroid = get_asteroid_by_name(asteroid_name)
    log(f"Asteroid mass before mining: {asteroid['mass']} kg", logging.INFO)

    extraction_rate = 1000  # Set the maximum extraction rate
    log(f"Mining asteroid...{asteroid_name}", logging.INFO)
    asteroid, total_elements_mined = mine_asteroid(asteroid, extraction_rate)
    log(f"Total elements mined: {sum([element['mined_mass_kg'] for element in total_elements_mined])} kg", logging.INFO)
    log(f"Asteroid mass after mining: {asteroid['mass']} kg", logging.INFO)

    # Uncomment the following line to update the asteroid in the database
    # update_asteroid(asteroid)