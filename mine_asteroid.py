"""
Description:
This script simulates extracting material from an asteroid over 1 hour, examines the contents of that material for known elements, and measures how much mass of each element has been extracted. Upon completion, the function updates the asteroid document with the updated elements and mined_mass_kg fields. Returns the updated asteroid document and a list of elements mined.

The script also includes functions to:
- Update the asteroid document in MongoDB with the updated elements and mass fields.

Functions:
- mine_hourly(asteroid: dict, extraction_rate: int, uid: str) -> (dict, list): Simulates extracting material from an asteroid, examines the contents for known elements, and measures the mass of each element extracted. Updates the asteroid document with the new elements and mined mass.
- update_mined_asteroid(asteroid: dict, mined_mass: int): Updates the asteroid document in MongoDB with the updated elements and mass fields.

Usage:
- The script can be run as a standalone module to simulate mining an asteroid and updating its document in MongoDB.
- Logging can be configured to output to the console or a file.
"""

import os
import random
from bson import Int64
from dotenv import load_dotenv
from datetime import datetime
from logging_config import logging  # Import logging configuration
from mongodb_config import asteroids_collection, mined_asteroids_collection  # Import MongoDB configuration

def mine_hourly(asteroid, extraction_rate, uid):
    """
    This function simulates mining an asteroid over 1 hour.
    """
    mined_mass = 0
    list_elements_mined = []
    extraction_rate = random.randint(1, extraction_rate)  # Randomize the extraction rate

    total_mass = sum(element["mass_kg"] for element in asteroid['elements'])
    for element in asteroid['elements']:
        if mined_mass >= extraction_rate:
            break

        element_mass_fraction = element["mass_kg"] / total_mass
        max_mineable_mass = min(extraction_rate - mined_mass, element["mass_kg"])
        actual_mined_mass = int(min(max_mineable_mass, element_mass_fraction * extraction_rate))

        element["mass_kg"] -= actual_mined_mass
        mined_mass += actual_mined_mass
        list_elements_mined.append({"name": element["name"], "mass_kg": actual_mined_mass})

        logging.info(f"Removed {actual_mined_mass} kg from {element['name']}.")

    asteroid['mass'] -= mined_mass
    asteroid['mined_elements_kg'] = Int64(mined_mass)
    asteroid['uid'] = uid

    return asteroid, list_elements_mined

def update_mined_asteroid(asteroid: dict, mined_mass: int):
    """
    This function updates the asteroid document in MongoDB with the updated elements and mass fields.
    """
    if "uid" not in asteroid:
        raise ValueError("Asteroid document must contain a 'uid' field.")

    # Remove the '_id' field if it exists
    asteroid.pop('_id', None)

    # Perform the $inc operation separately
    mined_asteroids_collection.update_one(
        {"full_name": asteroid["full_name"]},
        {"$inc": {"mined_elements_kg": Int64(mined_mass)}},
        upsert=True
    )

    # Perform the $set operation separately
    mined_asteroids_collection.update_one(
        {"full_name": asteroid["full_name"]},
        {"$set": asteroid},
        upsert=True
    )

if __name__ == "__main__":
    from find_asteroids import find_by_name

    asteroid_name = "101955 Bennu (1999 RQ36)"
    uid = "Brandon"
    logging.info(f"Retrieving asteroid info for {asteroid_name}")

    asteroid = find_by_name(asteroid_name)
    logging.info(f"Asteroid mass before mining: {asteroid['mass']} kg")

    extraction_rate = 1000  # Set the maximum extraction rate
    logging.info(f"Mining asteroid...{asteroid_name}")
    asteroid, total_elements_mined = mine_hourly(asteroid, extraction_rate, uid)
    mined_mass = sum([element['mass_kg'] for element in total_elements_mined])
    logging.info(f"Total elements mined: {mined_mass} kg")
    logging.info(f"Asteroid mass after mining: {asteroid['mass']} kg")

    # Update the asteroid in the mined_asteroids collection
    update_mined_asteroid(asteroid, mined_mass)