import os
import math
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv('MONGODB_URI')

def find_elements_use(elements: list, total_mined_mass: int) -> list:
    """
    This function processes the elements and categorizes them by their use.

    For each element, find it in the `asteroids.elements` collection. 
    Extract its `use` field and categorize the elements by their use.
    return a list of elements categorized by use and their total mass.
    """
    client = MongoClient(MONGODB_URI)
    db = client['asteroids']
    elements_collection = db['elements']

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

if __name__ == "__main__":
    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]
    total_mined_mass = 250
    elements_by_use = find_elements_use(sample_elements, total_mined_mass)
    pprint(elements_by_use)