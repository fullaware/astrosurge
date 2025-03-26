from datetime import datetime, timedelta
from bson import ObjectId
from modules.manage_ships import update_cargo, update_ship_attributes
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

    # Check if the mission is in a valid state to proceed
    if mission["status"] not in [MissionStatus.FUNDED.value, MissionStatus.EXECUTING.value]:
        logging.error(
            f"Mission {mission_id} cannot proceed. Current status: {mission['status']}. "
            f"Expected status: FUNDED or EXECUTING."
        )
        return False

    # If the mission is FUNDED, update its status to EXECUTING
    if mission["status"] == MissionStatus.FUNDED.value:
        logging.info(f"Mission {mission_id} is FUNDED. Updating status to EXECUTING.")
        missions_collection.update_one(
            {"_id": mission_id},
            {"$set": {"status": MissionStatus.EXECUTING.value}}
        )

    logging.info(f"Starting mission execution for mission ID {mission_id}.")

    # Simulate travel to the asteroid
    travel_days = mission["duration"] // 2
    for day in range(travel_days):
        logging.info(f"Day {day + 1}: Traveling to asteroid.")
        update_ship_attributes(mission["user_id"], {"location": mission["distance"] * (day + 1) / travel_days})
        log_event(mission_id, "travel", f"Day {day + 1}: Traveling to asteroid.")

    # Simulate mining
    logging.info("Mining asteroid...")
    mined_elements = []
    for day in range(1, travel_days + 1):
        daily_elements = []
        for hour in range(24):  # Simulate 24 hours of mining
            hourly_elements = mine_hourly(mission["asteroid_name"], mission["user_id"])
            daily_elements.extend(hourly_elements)
            log_event(mission_id, "mining", f"Hour {hour + 1}: Mined {hourly_elements}.")
        mined_elements.extend(daily_elements)
        update_cargo(mission["user_id"], daily_elements)  # Updated to use ship_id and daily_elements
        log_event(mission_id, "cargo_update", f"Day {day}: Updated cargo with {daily_elements}.")

    # Simulate return travel
    for day in range(travel_days):
        logging.info(f"Day {travel_days + day + 1}: Returning to Earth.")
        update_ship_attributes(mission["user_id"], mission["distance"] * (travel_days - day - 1) / travel_days)
        log_event(mission_id, "travel", f"Day {travel_days + day + 1}: Returning to Earth.")

    # Simulate depositing cargo
    logging.info("Depositing cargo on Earth...")
    deposit_cargo(mission["user_id"], mined_elements)
    log_event(mission_id, "cargo_deposit", f"Deposited cargo on Earth: {mined_elements}.")

    # Update mission status to SUCCESS
    missions_collection.update_one(
        {"_id": mission_id},
        {"$set": {"status": MissionStatus.SUCCESS.value, "mined_elements": mined_elements}}
    )
    log_event(mission_id, "mission_complete", f"Mission {mission_id} executed successfully.")
    logging.info(f"Mission {mission_id} executed successfully.")
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


def deposit_cargo(user_id: ObjectId, mined_elements: list):
    """
    Simulates depositing the mined cargo on Earth.

    Parameters:
    user_id (ObjectId): The user ID associated with the mission.
    mined_elements (list): The list of mined elements to deposit.

    Returns:
    None
    """
    # Logic to deposit cargo (e.g., update user's inventory or storage)
    logging.info(f"Depositing cargo for user {user_id}: {mined_elements}")


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