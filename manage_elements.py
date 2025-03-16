import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import find_elements  # Ensure find_elements is imported

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
leaderboard_collection = db["leaderboard"]

def update_leaderboard(uid: str, elements: list, total_mined_mass: int, total_value: float = 0):
    """
    This function updates the leaderboard with the mined elements by use and increments the mined value.

    Parameters:
    uid (str): The user id.
    elements (list): The list of elements mined.
    total_mined_mass (int): The total mass of elements mined.
    total_value (float): The total value of the mined elements.
    """
    try:
        # Find elements by use
        elements_by_use = find_elements.find_elements_use(elements, total_mined_mass)
        
        # Update the leaderboard
        for element in elements_by_use:
            leaderboard_collection.update_one(
                {"uid": uid},
                {"$inc": {f"uses.{element['use']}.mass_kg": element["total_mass_kg"]}},
                upsert=True
            )
        
        # Increment the mined value
        if total_value > 0:
            leaderboard_collection.update_one(
                {"uid": uid},
                {"$inc": {"mined_value": total_value}},
                upsert=True
            )
        
        logging.info(f"Leaderboard updated for uid: {uid}")
    except Exception as e:
        logging.error(f"Error updating leaderboard: {e}")

def sell_elements(uid: str, percentage: int, list_of_elements: list, commodity_values: dict):
    """
    This function sells a percentage of the specified elements and updates the leaderboard accordingly.

    Parameters:
    uid (str): The user id.
    percentage (int): The percentage of elements to sell.
    list_of_elements (list): The list of elements to sell.
    commodity_values (dict): The dictionary containing the market values of the elements.

    Returns:
    None
    """
    try:
        # Calculate the amount of each element to sell and their total value
        elements_to_sell = []
        total_value = 0
        for element in list_of_elements:
            mass_kg = element['mass_kg']
            sell_mass_kg = mass_kg * (percentage / 100.0)
            element_value = sell_mass_kg * commodity_values.get(element['name'].lower(), 0)
            total_value += element_value
            elements_to_sell.append({
                'name': element['name'],
                'mass_kg': sell_mass_kg
            })

        # Update the leaderboard with the sold elements and their total value
        update_leaderboard(uid, elements_to_sell, sum([e['mass_kg'] for e in elements_to_sell]), total_value)
        logging.info(f"Sold {percentage}% of elements for uid: {uid}")
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
    update_leaderboard(uid, sample_elements, total_mined_mass)

    # Example usage of sell_elements
    sell_elements(uid, 50, sample_elements, commodity_values)