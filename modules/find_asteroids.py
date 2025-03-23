import random
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import asteroids_collection  # Import MongoDB configuration

def find_by_full_name(full_name: str) -> dict:
    """
    Find an asteroid by its full name.

    Parameters:
    full_name (str): The full name of the asteroid.

    Returns:
    dict: The asteroid data if found, otherwise None.
    """
    asteroid = asteroids_collection.find_one({'full_name': full_name})
    if asteroid:
        logging.info(f"Asteroid found: {asteroid}")
        return asteroid
    logging.error(f"Asteroid with full name '{full_name}' not found.")
    return None

def find_by_distance(moid_days: int, num_asteroids: int = 3) -> tuple:
    """
    Find asteroids within a specified range of moid days.

    Parameters:
    moid_days (int): The moid in days.
    num_asteroids (int): The number of random asteroids to return.

    Returns:
    tuple: The total count of matching asteroids and a list of randomly selected asteroids.
    """
    logging.info(f"Querying asteroids with moid_days equal to {moid_days}")
    
    # Log the first few documents in the collection for debugging
    sample_asteroids = list(asteroids_collection.find().limit(5))
    logging.info(f"Sample asteroids from collection: {sample_asteroids}")
    
    # Log the moid_days field of each sample asteroid
    for asteroid in sample_asteroids:
        logging.info(f"Asteroid {asteroid['full_name']} has moid_days: {asteroid.get('moid_days')}")

    asteroids = list(asteroids_collection.find({
        'moid_days': moid_days
    }))
    total_count = len(asteroids)
    logging.info(f"Total asteroids found: {total_count}")
    if total_count > 0:
        selected_asteroids = random.sample(asteroids, min(num_asteroids, total_count))
        logging.info(f"Selected asteroids: {selected_asteroids}")
    else:
        selected_asteroids = []
    return total_count, selected_asteroids

if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example usage of find_by_full_name
    asteroid_full_name = "101955 Bennu (1999 RQ36)"  # Valid asteroid full name from asteroid_bennu.json
    asteroid = find_by_full_name(asteroid_full_name)
    logging.info(f"Asteroid: {asteroid}")

    # Example usage of find_by_distance
    moid_days = 10
    total_count, selected_asteroids = find_by_distance(moid_days)
    logging.info(f"Total asteroids found: {total_count}, Selected asteroids: {selected_asteroids}")