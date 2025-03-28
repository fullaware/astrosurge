from config.mongodb_config import MongoDBConfig
from config.logging_config import logging  # Updated logging import

# Use MongoDBConfig to get the asteroids collection
asteroids_collection = MongoDBConfig.get_collection("asteroids")

def find_by_full_name(name: str):
    logging.info(f"Finding asteroid by full name: {name}")
    return asteroids_collection.find_one({"full_name": name})

def find_by_distance(max_distance: float):
    logging.info(f"Finding asteroids within distance: {max_distance}")
    return list(asteroids_collection.find({"distance": {"$lte": max_distance}}))

def assess_asteroid_value(asteroid: dict):
    logging.info(f"Assessing value of asteroid: {asteroid.get('full_name', 'Unknown')}")
    resources = asteroid.get("resources", [])
    total_value = sum(resource["value"] * resource["mass"] for resource in resources)
    logging.info(f"Total value of asteroid: {total_value}")
    return total_value