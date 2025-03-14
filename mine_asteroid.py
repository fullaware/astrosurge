import os
import random
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
    return asteroids_collection.find_one({"full_name": asteroid_name}, {"_id": 0})

def mine_asteroid(asteroid: dict, extraction_rate: int) -> (dict, list):
    """
    This function simulates mining an asteroid by removing a random amount of mass (up to extraction_rate)
    from multiple elements in the asteroid's elements array and updating the asteroid's mass.
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

                print(Fore.GREEN + f"Removed {actual_mined_mass} kg from {element['name']}." + Style.RESET_ALL)
            else:
                print(Fore.RED + f"Not enough mass in {element['name']} to remove {actual_mined_mass} kg." + Style.RESET_ALL)
                asteroid["elements"].remove(element)
    else:
        print(Fore.RED + "No elements found in the asteroid." + Style.RESET_ALL)

    pprint(total_elements_mined)
    return asteroid, total_elements_mined

print(Fore.GREEN + "Retrieving asteroid by name..." + Style.RESET_ALL)
asteroid_name = "1 Ceres"
asteroid = get_asteroid_by_name(asteroid_name)
print(Fore.GREEN + f"Asteroid mass before mining: {asteroid['mass']} kg" + Style.RESET_ALL)

extraction_rate = 1000  # Set the maximum extraction rate
print(Fore.GREEN + "Mining asteroid..." + Style.RESET_ALL)
asteroid, total_elements_mined = mine_asteroid(asteroid, extraction_rate)
print(Fore.GREEN + f"Total elements mined: {sum([element['mined_mass_kg'] for element in total_elements_mined])} kg," + Style.RESET_ALL)
print(Fore.GREEN + f"Asteroid mass after mining: {asteroid['mass']} kg," + Style.RESET_ALL)
