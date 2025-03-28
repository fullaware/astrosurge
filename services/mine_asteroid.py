"""
Description:
This script simulates extracting material from an asteroid over 1 hour, examines the contents of that material for known elements, and measures how much mass of each element has been extracted. Upon completion, the function updates the asteroid document with the updated elements and mined_mass_kg fields. Returns the updated asteroid document and a list of elements mined.

The script also includes functions to:
- Update the asteroid document in MongoDB with the updated elements and mass fields.

Functions:
- mine_hourly(asteroid: dict, extraction_rate: int, user_id: ObjectId) -> (dict, list): Simulates extracting material from an asteroid, examines the contents for known elements, and measures the mass of each element extracted. Updates the asteroid document with the new elements and mined mass.
- update_mined_asteroid(asteroid: dict, mined_elements: list): Updates the asteroid document in MongoDB with the updated elements and mass fields.

Usage:
- The script can be run as a standalone module to simulate mining an asteroid and updating its document in MongoDB.
- Logging can be configured to output to the console or a file.
"""

from bson import ObjectId
from bson import Int64  # Import Int64 for 64-bit integers
from datetime import datetime
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import asteroids_collection, mined_asteroids_collection  # Import MongoDB configuration
import random  # Import random for generating random extraction rates

def get_asteroid_by_name(asteroid_name: str) -> dict:
    """
    Fetch an asteroid document from MongoDB by its full name.

    Parameters:
    asteroid_name (str): The name of the asteroid.

    Returns:
    dict: The asteroid document.
    """
    return asteroids_collection.find_one({'full_name': asteroid_name})

def get_mined_asteroid_by_name(asteroid_name: str, user_id: ObjectId) -> dict:
    """
    Retrieve a mined-asteroid copy in mined_asteroids collection by name and user.
    This function will NOT create a new copy; it only retrieves if it exists.

    Parameters:
    asteroid_name (str): The name of the asteroid.
    user_id (ObjectId): The user ID.

    Returns:
    dict: The mined asteroid document.
    """
    return mined_asteroids_collection.find_one({'full_name': asteroid_name, 'user_id': user_id})

def mine_hourly(asteroid_name: str, extraction_rate: int, user_id: ObjectId, ship_capacity: int, current_cargo_mass: int):
    """
    Mine elements from a cloned asteroid (in mined_asteroids) for one hour, respecting the ship's capacity.

    Parameters:
    asteroid_name (str): The name of the asteroid to mine.
    extraction_rate (int): The maximum rate at which to mine the asteroid.
    user_id (ObjectId): The ID of the user mining the asteroid.
    ship_capacity (int): The maximum capacity of the ship in kilograms.
    current_cargo_mass (int): The current mass of the cargo in the ship.

    Returns:
    tuple: (list of mined elements, bool indicating if the ship is at capacity)
    """
    # Retrieve or create the mined asteroid
    mined_asteroid = get_mined_asteroid_by_name(asteroid_name, user_id)
    if not mined_asteroid:
        original_asteroid = get_asteroid_by_name(asteroid_name)
        if not original_asteroid:
            logging.error(f"Asteroid '{asteroid_name}' not found in asteroids collection.")
            return [], False
        
        # Create a new mined asteroid
        mined_asteroid = {
            '_id': ObjectId(),
            'name': original_asteroid['name'],
            'full_name': original_asteroid['full_name'],
            'elements': original_asteroid.get('elements', []),
            'total_mass': original_asteroid.get('total_mass', 0),
            'mass': original_asteroid.get('mass', 0),
            'distance': original_asteroid.get('distance', 0),
            'last_mined': None,
            'user_id': user_id,
            'original_asteroid_id': original_asteroid['_id'],
        }
        mined_asteroids_collection.insert_one(mined_asteroid)
        logging.info(f"Created new mined asteroid for '{asteroid_name}'.")

    # Perform mining
    mined_elements = []
    total_mined_mass = 0
    remaining_capacity = ship_capacity - current_cargo_mass

    logging.info(f"Starting mining on asteroid '{asteroid_name}' with remaining capacity: {remaining_capacity}")
    while remaining_capacity > 0:
        # Randomly select an element from the asteroid's elements
        if not mined_asteroid['elements']:
            logging.warning(f"No elements available to mine on asteroid '{asteroid_name}'.")
            break

        element = random.choice(mined_asteroid['elements'])
        element_name = element['name']

        # Generate a random extraction rate for this mining operation
        random_extraction_rate = random.randint(1, extraction_rate)

        # Determine the mined mass for this element
        mined_mass = min(random_extraction_rate, remaining_capacity, element.get('mass_kg', 0))
        if mined_mass <= 0:
            logging.warning(f"Element '{element_name}' has no remaining mass to mine.")
            mined_asteroid['elements'].remove(element)  # Remove depleted element
            continue

        remaining_capacity -= mined_mass
        total_mined_mass += mined_mass
        element['mass_kg'] -= mined_mass

        # Check if the element already exists in the mined elements list
        existing_element = next((e for e in mined_elements if e["name"] == element_name), None)
        if existing_element:
            existing_element["mass_kg"] += mined_mass
        else:
            mined_elements.append({"name": element_name, "mass_kg": mined_mass})

        logging.info(f"Mined {mined_mass} kg of {element_name}. Remaining capacity: {remaining_capacity}")

    # Remove depleted elements from the asteroid's elements list
    mined_asteroid['elements'] = [e for e in mined_asteroid['elements'] if e.get('mass_kg', 0) > 0]

    mined_asteroid['total_mass'] -= total_mined_mass
    mined_asteroid['last_mined'] = datetime.now()

    # Ensure mined_elements mass_kg is Int64
    for element in mined_elements:
        element["mass_kg"] = Int64(element["mass_kg"])

    # Update the mined asteroid in the database
    mined_asteroids_collection.update_one(
        {'_id': mined_asteroid['_id']},
        {
            '$set': {
                'elements': mined_asteroid['elements'],
                'total_mass': mined_asteroid['total_mass'],
                'last_mined': mined_asteroid['last_mined']
            },
            '$inc': {
                'total_mined_mass': total_mined_mass
            }
        }
    )

    logging.info(f"Asteroid mined (copy in mined_asteroids): {mined_asteroid['_id']}, total mined mass: {total_mined_mass}")
    return mined_elements, remaining_capacity == 0

def update_mined_asteroid(asteroid: dict, mined_elements: list):
    """
    Update the asteroid document in MongoDB with the updated elements and mass fields.

    Parameters:
    asteroid (dict): The asteroid document.
    mined_elements (list): The list of mined elements.

    Returns:
    None
    """
    # Raise an error if any mined element is missing 'mass_kg'
    for element in mined_elements:
        if 'mass_kg' not in element:
            logging.error(f"Mined element missing 'mass_kg': {element}")
            raise ValueError("Mined element is missing required 'mass_kg' field.")

    mined_mass = sum(element['mass_kg'] for element in mined_elements if isinstance(element, dict))

    asteroids_collection.update_one(
        {'_id': asteroid['_id']},
        {'$set': {'elements': asteroid['elements'], 'total_mass': asteroid['total_mass'], 'last_mined': asteroid['last_mined']}}
    )
    mined_asteroids_collection.update_one(
        {'_id': asteroid['_id']},
        {'$inc': {'total_mined_mass': mined_mass}}
    )
    logging.info(f"Asteroid updated: {asteroid['_id']}, mined mass: {mined_mass}")

if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example asteroid document
    example_asteroid = {
        '_id': ObjectId("60d5f9b8f8d2f8a0b8f8d2f8"),  # Example ObjectId
        'name': 'Example Asteroid',
        'elements': [{'name': 'Iron', 'mass_kg': 1000}, {'name': 'Nickel', 'mass_kg': 500}],
        'total_mass': 1500,
        'last_mined': None
    }

    # Example usage of mine_hourly
    user_id = ObjectId("60d5f9b8f8d2f8a0b8f8d2f8")  # Example ObjectId
    mined_elements, is_at_capacity = mine_hourly('Example Asteroid', 100, user_id, 2000, 500)
    logging.info(f"Mined elements: {mined_elements}, Ship at capacity: {is_at_capacity}")

    # Example usage of update_mined_asteroid
    update_mined_asteroid(example_asteroid, mined_elements)
    logging.info("Script finished.")