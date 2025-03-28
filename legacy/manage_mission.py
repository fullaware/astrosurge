"""
## Manage Missions

- **Locate asteroids** and assess their value to choose which asteroid is best.
- **Choose Ship**
- **Estimate mission costs**
- **Travel to asteroid**
- **Mine asteroid**
- **Travel to Earth with resources**
- **Sell/Distribute mined resources**
- **Ship Maintenance**

"""

import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId
from amos.find_value import assess_asteroid_value
from amos.mine_asteroid import mine_hourly, update_mined_asteroid
from manage_elements import find_elements_use, sell_elements
from pprint import pprint
import uuid
from datetime import datetime, timezone

# Configure logging to show INFO level messages on the screen
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collection
db = mongodb_client["asteroids"]  
missions_collection = db["missions"]
users_collection = db["users"]
ships_collection = db["ships"]
asteroids_collection = db["asteroids"]
elements_collection = db["elements"]

def get_missions(uid: str):
    """
    Get all missions for a given user id.

    Parameters:
    uid (str): The user id associated with the missions.

    Returns:
    list: A list of mission documents.
    """
    missions = missions_collection.find({"uid": uid})
    return list(missions)

def plan_mission(uid: str, asteroid_name: str, distance: int, investment_level: int):
    """
    Plan the entire mission:
    1) Estimate cost
    2) Find asteroid to estimate reward
    3) Travel to asteroid
    4) Mine asteroid
    5) Travel back to Earth
    6) Sell elements
    7) Repeat if desired
    """
    # 1) ESTIMATE MISSION COST
    logging.info(f"Estimating mission cost. Investment level: {investment_level}")
    # (Example cost calculation, adjust as needed)
    base_cost = 150_000_000
    travel_cost_factor = distance * 5000
    total_cost = base_cost + travel_cost_factor
    if investment_level < total_cost:
        logging.error("Insufficient funds for this mission.")
        return None

    # 2) FIND ASTEROID TO ESTIMATE REWARD
    logging.info(f"Finding asteroid: {asteroid_name}")
    # (Your logic to handle multiple asteroids or a single one)
    asteroid = asteroids_collection.find_one({"full_name": asteroid_name})
    if not asteroid:
        logging.error(f"Asteroid {asteroid_name} not found.")
        return None

    # Parse the "elements" field if it's a JSON string
    if isinstance(asteroid["elements"], str):
        import json
        asteroid["elements"] = json.loads(asteroid["elements"])

    # Now asteroid["elements"] should be a list or dict, and can be iterated safely
    
    # Evaluate potential reward
    estimated_value = assess_asteroid_value(asteroid)
    logging.info(f"Asteroid value estimated at: {estimated_value}")

    # 3) TRAVEL TO ASTEROID
    logging.info("Choosing ship and traveling to asteroid.")
    ship = {
        'oid': str(uuid.uuid4()),
        'name': "MissionShip",
        'uid': uid,
        'shield': 100,
        'mining_power': 1000,
        'capacity': 1000,  # Add capacity here
        'created': datetime.now(timezone.utc),
        'days_in_service': 0,
        'location': distance,
        'mission': 0,
        'hull': 100,
        'cargo': {}
    }

    # 4) MINE ASTEROID
    logging.info("Mining asteroid.")
    mined_elements = mine_asteroid(asteroid_name, ship['capacity'], uid)
    update_cargo(ship['oid'], mined_elements)
    update_mined_asteroid(asteroid_name, mined_elements)

    # 5) TRAVEL BACK TO EARTH
    ship['location'] = 0
    logging.info("Ship returned to Earth.")

    # 6) SELL ELEMENTS
    total_mined_mass = sum(item['mass_kg'] for item in mined_elements)
    find_elements_use(mined_elements, total_mined_mass)
    update_users(uid, mined_elements, total_mined_mass, estimated_value)
    sell_elements(uid, 50, mined_elements, ship.get('commodity_values', {}))

    # 7) REPEAT - In practice, user can be prompted or the function can loop
    logging.info("Mission completed. Ready to plan the next.")

    # Return any relevant mission details
    return {
        "asteroid": asteroid_name,
        "estimated_value": estimated_value,
        "cost": total_cost,
        "mined_elements": mined_elements
    }

def example_usage():
    """
    Example usage of the mission plan, for demonstration purposes.
    """
    user_name = "Alice"
    user_password = "secure_password"

    # Authenticate user
    uid = get_user(user_name, user_password)
    if not uid or not auth_user(uid, user_password):
        logging.error("Authentication failed.")
        return

    # Plan and execute mission
    mission_result = plan_mission(uid, "1 Ceres", distance=35, investment_level=300_000_000)
    logging.info(f"Mission result: {mission_result}")

if __name__ == "__main__":
    example_usage()
