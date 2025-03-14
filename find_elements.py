import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv('MONGODB_URI')

def find_elements(elements: list) -> list:
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

    for use, total_mass in usecases_dict.items():
        elements_by_use.append({
            "use": use,
            "total_mass_kg": total_mass
        })

    return elements_by_use

if __name__ == "__main__":
    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]
    elements_by_use = find_elements(sample_elements)
    pprint(elements_by_use)