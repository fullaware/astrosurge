from datetime import datetime, timedelta
from bson import ObjectId
from modules.manage_ships import get_ship, update_ship_cargo, ships_collection
from modules.mine_asteroid import mine_hourly
from modules.manage_mission import MissionStatus, missions_collection
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


def deposit_cargo(mission_id: ObjectId, mined_elements: list):
    """
    Simulates depositing the mined cargo for a specific mission.

    Parameters:
    mission_id (ObjectId): The mission ID associated with the deposit.
    mined_elements (list): The list of mined elements to deposit.

    Returns:
    None
    """
    if not mined_elements:
        logging.info(f"No mined elements to deposit for mission {mission_id}.")
        return

    # Update the mission's mined_elements in the database
    for element in mined_elements:
        name = element.get("name")
        mass_kg = element.get("mass_kg", 0)

        if not name or mass_kg <= 0:
            logging.warning(f"Invalid mined element: {element}. Skipping.")
            continue

        # Increment the mass of the existing element in the mission's mined_elements or add it if it doesn't exist
        result = missions_collection.update_one(
            {"_id": mission_id, "mined_elements.name": name},  # Match the mission and the specific mined element
            {"$inc": {"mined_elements.$.mass_kg": mass_kg}},  # Increment the mass of the existing element
        )

        # If the element doesn't exist, add it to the mined_elements array
        if result.matched_count == 0:
            missions_collection.update_one(
                {"_id": mission_id},  # Match the mission
                {"$push": {"mined_elements": {"name": name, "mass_kg": mass_kg}}},  # Add the new element
            )

    logging.info(f"Deposited cargo for mission {mission_id}: {mined_elements}")


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