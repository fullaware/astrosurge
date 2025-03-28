from models import AsteroidModel
from config.mongodb_config import MongoDBConfig
from config.logging_config import logging  # Updated logging import

asteroids_collection = MongoDBConfig.get_collection("asteroids")

def find_by_full_name(name: str) -> AsteroidModel:
    """
    Find an asteroid by its full name and validate it against the Pydantic model.
    """
    logging.info(f"Finding asteroid by full name: {name}")
    asteroid = asteroids_collection.find_one({"full_name": name})
    if asteroid:
        return AsteroidModel(**asteroid)
    return None

def find_by_distance(max_distance: float):
    """
    Find asteroids within a maximum distance from Earth.
    """
    logging.info(f"Finding asteroids within distance: {max_distance}")
    asteroids = asteroids_collection.find({"distance": {"$lte": max_distance}})
    return [AsteroidModel(**asteroid) for asteroid in asteroids]

def assess_asteroid_value(asteroid: dict):
    logging.info(f"Assessing value of asteroid: {asteroid.get('full_name', 'Unknown')}")
    resources = asteroid.get("resources", [])
    total_value = sum(resource["value"] * resource["mass"] for resource in resources)
    logging.info(f"Total value of asteroid: {total_value}")
    return total_value