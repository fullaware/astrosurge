import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import math
import uuid

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

def update_users(uid: str, elements: list, total_mined_mass: int, total_value: int = 0):
    """
    This function updates the users collection with the mined elements by use and increments the mined value.

    Parameters:
    uid (str): The user id.
    elements (list): The list of elements mined.
    total_mined_mass (int): The total mass of elements mined.
    total_value (int): The total value of the mined elements.
    """
    try:
        # Find elements by use
        elements_by_use = find_elements_use(elements, total_mined_mass)
        
        # Update the users collection
        for element in elements_by_use:
            users_collection.update_one(
                {"uid": uid},
                {"$inc": {f"uses.{element['use']}.mass_kg": int(element["total_mass_kg"])}},
                upsert=True
            )
        
        # Increment the mined value
        if total_value > 0:
            users_collection.update_one(
                {"uid": uid},
                {"$inc": {"mined_value": int(total_value)}},
                upsert=True
            )
        
        logging.info(f"Users collection updated for uid: {uid}")
    except Exception as e:
        logging.error(f"Error updating users collection: {e}")

def get_user(name: str) -> str:
    """
    Get or create a user with the given name. If the user exists, return the existing uid.
    Otherwise, create a new user with the specified name and a bank balance of 0, and return the new uid.

    Parameters:
    name (str): The name of the user.

    Returns:
    str: The uid of the user.
    """
    user = users_collection.find_one({'name': name})
    if user:
        logging.info(f"User with name '{name}' already exists: {user}")
        return user['uid']

    uid = str(uuid.uuid4())
    new_user = {
        'uid': uid,
        'name': name,
        'bank': 0
    }
    users_collection.insert_one(new_user)
    logging.info(f"New user added: {new_user}")
    return uid

if __name__ == "__main__":

    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]
    total_mined_mass = 250
    

    # Example usage of get_user
    user_name = "Alice"
    user_uid = get_user(user_name)
    update_users(user_uid, sample_elements, total_mined_mass)
    print(f"User UID for {user_name}: {user_uid}")