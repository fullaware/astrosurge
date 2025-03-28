from models import AsteroidModel
from config.mongodb_config import MongoDBConfig
from config.logging_config import logging  # Updated logging import

# Get the MongoDB collection for asteroids
asteroids_collection = MongoDBConfig.get_collection("asteroids")

def find_by_full_name(name: str) -> AsteroidModel:
    """
    Find an asteroid by its full name and validate it against the Pydantic model.

    Parameters:
    - name (str): The full name of the asteroid.

    Returns:
    - AsteroidModel: The validated asteroid data, or None if not found.
    """
    logging.info(f"Searching for asteroid by full name: {name}")
    asteroid = asteroids_collection.find_one({"full_name": name})
    if asteroid:
        logging.info(f"Asteroid found: {name}")
        return AsteroidModel(**asteroid)
    logging.warning(f"Asteroid not found: {name}")
    return None

def find_by_distance(max_distance: float):
    """
    Find asteroids within a maximum distance from Earth.

    Parameters:
    - max_distance (float): The maximum distance (in days) to filter asteroids.

    Returns:
    - List[AsteroidModel]: A list of validated asteroid data.
    """
    logging.info(f"Searching for asteroids within distance: {max_distance}")
    asteroids = asteroids_collection.find({"distance": {"$lte": max_distance}})
    asteroid_list = [AsteroidModel(**asteroid) for asteroid in asteroids]
    logging.info(f"Found {len(asteroid_list)} asteroids within distance: {max_distance}")
    return asteroid_list

def assess_asteroid_value(asteroid: dict) -> int:
    """
    Assess the total value of an asteroid based on its resources.

    Parameters:
    - asteroid (dict): The asteroid data.

    Returns:
    - int: The total value of the asteroid.
    """
    logging.info(f"Assessing value of asteroid: {asteroid.get('full_name', 'Unknown')}")
    resources = asteroid.get("resources", [])
    total_value = sum(resource["value"] * resource["mass_kg"] for resource in resources)
    logging.info(f"Total value of asteroid '{asteroid.get('full_name', 'Unknown')}': {total_value}")
    return total_value