import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId
from manage_users import get_user, auth_user, update_users
from manage_ship import get_ship, update_cargo, list_cargo, empty_cargo, repair_ship
from find_asteroids import find_asteroids
from find_value import assess_asteroid_value
from mine_asteroid import mine_asteroid, update_mined_asteroid
from manage_elements import find_elements_use, sell_elements
from pprint import pprint

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

def plan_mission(uid: str, ship_capacity: int, estimated_value: int, mission_duration: int, investment_level: int, asteroid_full_name: str, mined_elements: list):
    """
    Plan a mission based on ship capacity, estimated value of elements, mission duration, investment level, asteroid full_name, and mined elements.

    Parameters:
    uid (str): The user id.
    ship_capacity (int): The capacity of the ship.
    estimated_value (int): The estimated value of elements.
    mission_duration (int): The duration of the mission in days.
    investment_level (int): The level of investment.
    asteroid_full_name (str): The full name of the asteroid.
    mined_elements (list): The list of mined elements and their values.

    Returns:
    dict: The mission details.
    """
    ship_cost = 150000000  # $150M
    operational_cost_per_day = 500000  # Example operational cost per day
    total_operational_cost = mission_duration * operational_cost_per_day
    total_cost = ship_cost + total_operational_cost

    # Calculate repayment rate based on mission success or failure
    repayment_rate = 1.5  # Initial repayment rate
    user = users_collection.find_one({'uid': uid})
    if user:
        last_mission = missions_collection.find_one({'uid': uid}, sort=[('_id', -1)])
        if last_mission and last_mission.get('status') == 2:
            repayment_rate = 1.25
        else:
            repayment_rate = 1.75

    # Calculate total repayment amount
    total_repayment = total_cost * repayment_rate

    # Check if the user can afford the mission
    if investment_level < total_cost:
        logging.error(f"Insufficient investment level for mission. Required: {total_cost}, Provided: {investment_level}")
        return None

    # Ensure the user has a ship
    ship = ships_collection.find_one({'uid': uid})
    if not ship:
        logging.error(f"No ship found for user {uid}.")
        return None

    # Create mission details
    mission_details = {
        'uid': uid,
        'ship_capacity': ship_capacity,
        'estimated_value': estimated_value,
        'mission_duration': mission_duration,
        'investment_level': investment_level,
        'total_cost': total_cost,
        'total_repayment': total_repayment,
        'repayment_rate': repayment_rate,
        'status': 0,  # 0 = planned
        'asteroid_full_name': asteroid_full_name,
        'mined_elements': mined_elements
    }

    # Insert mission details into the database
    result = missions_collection.insert_one(mission_details)
    mission_details['_id'] = result.inserted_id
    logging.info(f"Mission planned: {mission_details}")
    return mission_details

def execute_mission(uid: str, mission_id: str):
    """
    Execute a mission by traveling to the asteroid, mining it, and returning to Earth.

    Parameters:
    uid (str): The user id.
    mission_id (str): The mission id.

    Returns:
    bool: True if the mission was successful, False otherwise.
    """
    mission = missions_collection.find_one({'_id': ObjectId(mission_id)})
    if not mission:
        logging.error(f"Mission with id {mission_id} not found.")
        return False

    # Travel to asteroid and mine it
    ship = ships_collection.find_one({'uid': uid})
    if not ship:
        logging.error(f"No ship found for user {uid}.")
        return False

    mined_elements = claim_asteroid(mission['asteroid_full_name'], ship['capacity'])
    update_cargo(ship['oid'], mined_elements)

    # Travel back to Earth
    ship['location'] = 0  # Assume 0 is Earth

    # Sell/Distribute mined resources
    total_mined_mass = sum(element['mass_kg'] for element in mined_elements)
    elements_by_use = find_elements_use(mined_elements, total_mined_mass)
    update_users(uid, mined_elements, total_mined_mass, mission['estimated_value'])
    sell_elements(uid, 50, mined_elements, ship['commodity_values'])

    return True

def complete_mission(uid: str, mission_id: str, success: bool):
    """
    Complete a mission and update the user's repayment rate based on mission success or failure.

    Parameters:
    uid (str): The user id.
    mission_id (str): The mission id.
    success (bool): Whether the mission was successful.

    Returns:
    None
    """
    mission = missions_collection.find_one({'_id': ObjectId(mission_id)})
    if not mission:
        logging.error(f"Mission with id {mission_id} not found.")
        return

    # Update mission status
    status = 2 if success else 4  # 2 = Success, 4 = Failed
    missions_collection.update_one({'_id': ObjectId(mission_id)}, {'$set': {'status': status, 'success': success}})

    # Update user's repayment rate based on mission success or failure
    if success:
        users_collection.update_one({'uid': uid}, {'$set': {'mission_success': True}})
        repair_ship(uid)  # Repair the ship if the mission is successful
    else:
        users_collection.update_one({'uid': uid}, {'$set': {'mission_success': False}})
        # Purchase a new ship if the mission fails
        new_ship = {
            'uid': uid,
            'status': 'new',
            'cost': 150000000  # $150M
        }
        ships_collection.insert_one(new_ship)
        logging.info(f"New ship purchased for user {uid}.")

    logging.info(f"Mission {mission_id} completed. Success: {success}")

def initiate_mission(user_name: str, user_password: str):
    """
    Initiate a mission by finding and valuing asteroids, planning the mission, and completing it.

    Parameters:
    user_name (str): The name of the user.
    user_password (str): The password of the user.

    Returns:
    None
    """
    # Authenticate user
    user_uid = get_user(user_name, user_password)
    if not auth_user(user_uid, user_password):
        logging.error("Authentication failed.")
        return

    # Find and value 3 asteroids
    distance = 20
    total_count, asteroid_list = find_asteroids(distance, distance, 3)
    if total_count < 3:
        logging.error("Not enough asteroids found.")
        return

    asteroid_values = []
    for asteroid in asteroid_list:
        if 'elements' not in asteroid or not isinstance(asteroid['elements'], list):
            logging.error(f"Asteroid {asteroid['full_name']} does not contain a valid 'elements' key.")
            continue
        value = assess_asteroid_value(asteroid)
        asteroid_values.append((asteroid['full_name'], value))

    if not asteroid_values:
        logging.error("No valid asteroids found.")
        return

    # Choose the most valuable asteroid
    asteroid_values.sort(key=lambda x: x[1], reverse=True)
    chosen_asteroid = asteroid_values[0]
    asteroid_full_name = chosen_asteroid[0]
    estimated_value = chosen_asteroid[1]

    # Ensure the user has a ship
    ship = ships_collection.find_one({'uid': user_uid})
    if not ship:
        ship = create_ship(user_uid, "Merlin")
        logging.info(f"New ship created for user {user_uid}.")

    # Plan the mission
    ship_capacity = ship['capacity']
    mission_duration = 30
    investment_level = 200000000
    mined_elements = claim_asteroid(asteroid_full_name, ship_capacity)
    mission_details = plan_mission(user_uid, ship_capacity, estimated_value, mission_duration, investment_level, asteroid_full_name, mined_elements)
    if not mission_details:
        logging.error("Mission planning failed.")
        return

    # Execute the mission
    success = execute_mission(user_uid, mission_details['_id'])

    # Complete the mission
    complete_mission(user_uid, mission_details['_id'], success)

    # Ship maintenance
    empty_cargo(ship['oid'], user_uid)
    repair_ship(ship['oid'], user_uid)

if __name__ == "__main__":
    # Example usage of initiate_mission
    initiate_mission("Alice", "secure_password")

