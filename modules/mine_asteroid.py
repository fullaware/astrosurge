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
from datetime import datetime
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import asteroids_collection, mined_asteroids_collection  # Import MongoDB configuration

def mine_hourly(asteroid: dict, extraction_rate: int, user_id: ObjectId) -> (dict, list):
    """
    Simulate extracting material from an asteroid over 1 hour.

    Parameters:
    asteroid (dict): The asteroid document.
    extraction_rate (int): The maximum extraction rate.
    user_id (ObjectId): The user ID.

    Returns:
    (dict, list): The updated asteroid document and a list of elements mined.
    """
    mined_elements = []
    total_mined_mass = 0

    # Raise an error if any element is missing 'mass_kg'
    for element in asteroid['elements']:
        if 'mass_kg' not in element:
            logging.error(f"Element missing 'mass_kg': {element}")
            raise ValueError("Element is missing required 'mass_kg' field.")

        mined_mass = min(extraction_rate, element['mass_kg'])
        total_mined_mass += mined_mass
        element['mass_kg'] -= mined_mass
        mined_elements.append({'name': element['name'], 'mass_kg': mined_mass})

    if 'total_mass' not in asteroid:
        asteroid['total_mass'] = sum(element['mass_kg'] for element in asteroid['elements'])

    asteroid['total_mass'] -= total_mined_mass
    asteroid['last_mined'] = datetime.now()

    # Update the asteroid document in MongoDB
    asteroids_collection.update_one(
        {'_id': asteroid['_id']},
        {'$set': {'elements': asteroid['elements'], 'total_mass': asteroid['total_mass'], 'last_mined': asteroid['last_mined']}}
    )

    # Update the mined_asteroids_collection
    mined_asteroid = mined_asteroids_collection.find_one({'_id': asteroid['_id']})
    if mined_asteroid:
        mined_asteroids_collection.update_one(
            {'_id': asteroid['_id']},
            {'$inc': {'total_mined_mass': total_mined_mass}}
        )
    else:
        mined_asteroids_collection.insert_one({
            '_id': asteroid['_id'],
            'name': asteroid['name'],
            'total_mined_mass': total_mined_mass,
            'user_id': user_id
        })

    logging.info(f"Asteroid mined: {asteroid['_id']}, total mined mass: {total_mined_mass}")
    return asteroid, mined_elements

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
    updated_asteroid, mined_elements = mine_hourly(example_asteroid, 100, user_id)
    logging.info(f"Updated asteroid: {updated_asteroid}, mined elements: {mined_elements}")

    # Example usage of update_mined_asteroid
    update_mined_asteroid(updated_asteroid, mined_elements)
    logging.info("Script finished.")