import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import math
from pprint import pprint

# Configure logging to show INFO level messages on the screen
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collection
db = mongodb_client["asteroids"]  # Replace with your actual database name
users_collection = db["users"]
elements_collection = db["elements"]

def find_elements_use(elements: list, total_mined_mass: int) -> list:
    """
    This function processes the elements and categorizes them by their use.

    For each element, find it in the `asteroids.elements` collection. 
    Extract its `use` field and categorize the elements by their use.
    return a list of elements categorized by use and their total mass.
    """
    elements_by_use = []
    usecases_dict = {}

    for element in elements:
        element_name = element.get('name')
        mass_kg = element.get('mass_kg')

        db_element = elements_collection.find_one({'name': element_name})
        if db_element:
            uses = db_element.get('uses', [])
            for use in uses:
                if use not in usecases_dict:
                    usecases_dict[use] = 0
                usecases_dict[use] += mass_kg

    # Ensure the total mass allocated to each use is less than the total mined mass
    total_allocated_mass = sum(usecases_dict.values())
    if total_allocated_mass > total_mined_mass:
        scale_factor = total_mined_mass / total_allocated_mass
        for use in usecases_dict:
            usecases_dict[use] *= scale_factor

    for use, total_mass in usecases_dict.items():
        elements_by_use.append({
            "use": use,
            "total_mass_kg": math.ceil(total_mass)
        })

    return elements_by_use

def sell_elements(uid: str, percentage: int, cargo_list: list, commodity_values: dict):
    """
    Sell a percentage of each element in the cargo list.

    Parameters:
    uid (str): The user id.
    percentage (int): The percentage of each element to sell.
    cargo_list (list): The list of elements in the cargo.
    commodity_values (dict): The dictionary of commodity values.

    Returns:
    None
    """
    try:
        total_value = 0
        for element in cargo_list:
            element_name = element['name']
            mass_kg = element['mass_kg']
            value_per_kg = commodity_values.get(element_name.lower(), 0)
            sell_mass = mass_kg * (percentage / 100)
            sell_value = sell_mass * value_per_kg
            total_value += sell_value
            logging.info(f"Sold {sell_mass} kg of {element_name} for {sell_value} $")

        # Deduct the total value from the user's bank balance
        users_collection.update_one(
            {"uid": uid},
            {"$inc": {"bank": int(total_value)}},
            upsert=True
        )

        logging.info(f"Total value of sold elements: {total_value} $")
    except Exception as e:
        logging.error(f"Error selling elements: {e}")

if __name__ == "__main__":
    uid = "Brandon"
    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]
    total_mined_mass = 250
    commodity_values = {
        'hydrogen': 10,  # Example values
        'oxygen': 20
    }

    # Example usage of sell_elements
    sell_elements(uid, 50, sample_elements, commodity_values)

    # Example usage of find_elements_use
    elements_by_use = find_elements_use(sample_elements, total_mined_mass)
    pprint(elements_by_use)