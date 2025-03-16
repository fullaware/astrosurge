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
users_collection = db["users"]

def update_users(uid: str, elements: list, total_mined_mass: int, total_value: float = 0):
    """
    This function updates the users collection with the mined elements by use and increments the mined value.

    Parameters:
    uid (str): The user id.
    elements (list): The list of elements mined.
    total_mined_mass (int): The total mass of elements mined.
    total_value (float): The total value of the mined elements.
    """
    try:
        # Find elements by use
        elements_by_use = find_elements.find_elements_use(elements, total_mined_mass)
        
        # Update the users collection
        for element in elements_by_use:
            users_collection.update_one(
                {"uid": uid},
                {"$inc": {f"uses.{element['use']}.mass_kg": element["total_mass_kg"]}},
                upsert=True
            )
        
        # Increment the mined value
        if total_value > 0:
            users_collection.update_one(
                {"uid": uid},
                {"$inc": {"mined_value": total_value}},
                upsert=True
            )
        
        logging.info(f"Users collection updated for uid: {uid}")
    except Exception as e:
        logging.error(f"Error updating users collection: {e}")

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
            {"$inc": {"bank": total_value}},
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
    update_users(uid, sample_elements, total_mined_mass)

    # Example usage of sell_elements
    sell_elements(uid, 50, sample_elements, commodity_values)