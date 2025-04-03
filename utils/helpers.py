import logging
import random
from config import MongoDBConfig

db = MongoDBConfig.get_database()

def get_random_asteroids(travel_days: int, limit: int = 3) -> list[dict]:
    logging.info(f"Fetching asteroids with moid_days = {travel_days}")
    matching_asteroids = list(db.asteroids.find({"moid_days": travel_days}))
    if not matching_asteroids:
        logging.warning(f"No asteroids found with moid_days = {travel_days}")
        return []
    return random.sample(matching_asteroids, min(limit, len(matching_asteroids)))