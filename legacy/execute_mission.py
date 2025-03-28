from datetime import datetime, timedelta
from bson import ObjectId, Int64  # Import Int64 for 64-bit integers
from amos.manage_ships import get_ship, update_ship_cargo, ships_collection
from amos.mine_asteroid import mine_hourly
from amos.manage_mission import MissionStatus, missions_collection
from config.mongodb_config import events_collection  # Import the events collection
from config.logging_config import logging


def execute_mission(mission_id: ObjectId):
    """
    Executes a mission by simulating travel, mining, and returning to Earth.

    Parameters:
    mission_id (ObjectId): The mission ID.

    Returns:
    bool: True if the mission was successfully executed, False otherwise.
    """
    mission = missions_collection.find_one({"_id": mission_id})
    if not mission:
        logging.error(f"Mission with ID {mission_id} not found.")
        return False

    ship_id = mission["ship_id"]
    ship = get_ship(ship_id)
    if not ship:
        logging.error(f"Ship with ID {ship_id} not found.")
        return False

    # Get ship capacity and current cargo mass
    ship_capacity = ship.get('capacity', 50000)  # Default to 50,000 kg
    current_cargo_mass = sum(item['mass_kg'] for item in ship.get('cargo', []))

    # Perform mining
    mined_elements = mine_hourly(
        asteroid_name=mission["asteroid_name"],
        extraction_rate=ship.get("mining_power", 100),  # Default mining power
        user_id=mission["user_id"],
        ship_capacity=ship_capacity,
        current_cargo_mass=current_cargo_mass
    )

    # Handle mined elements (e.g., update cargo, log events, etc.)
    update_ship_cargo(ship_id, mined_elements)
    logging.info(f"Mined elements added to ship cargo: {mined_elements}")
    return True


def log_event(mission_id: ObjectId, event_type: str, description: str):
    """
    Logs an event to the asteroids.events collection.

    Parameters:
    mission_id (ObjectId): The mission ID associated with the event.
    event_type (str): The type of event (e.g., "travel", "mining", "cargo_update").
    description (str): A description of the event.

    Returns:
    None
    """
    event = {
        "mission_id": mission_id,
        "event_type": event_type,
        "description": description,
        "timestamp": datetime.utcnow()
    }
    events_collection.insert_one(event)
    logging.info(f"Logged event: {event}")


def deposit_cargo(mission_id: ObjectId, cargo: list):
    """
    Deposits the cargo into the mission's mined_elements.

    Parameters:
    mission_id (ObjectId): The mission ID.
    cargo (list): The cargo to deposit.

    Returns:
    None
    """
    for item in cargo:
        item["mass_kg"] = Int64(item["mass_kg"])  # Convert to Int64

    missions_collection.update_one(
        {"_id": mission_id},
        {"$push": {"mined_elements": {"$each": cargo}}}
    )
    logging.info(f"Cargo deposited into mission ID '{mission_id}'.")


if __name__ == "__main__":
    # Example mission ID to test
    test_mission_id = ObjectId("67e3fdf07c877f151acbf810")  # Replace with a valid mission ID from your database

    # Execute the mission
    try:
        success = execute_mission(test_mission_id)
        if success:
            logging.info(f"Mission {test_mission_id} executed successfully.")
        else:
            logging.error(f"Mission {test_mission_id} execution failed.")
    except Exception as e:
        logging.error(f"An error occurred while executing the mission: {e}")