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

from config.logging_config import logging  # Import logging configuration
from modules.manage_users import update_users
from modules.manage_ships import create_ship, get_ships_by_user_id
from modules.find_asteroids import find_by_full_name
from modules.find_value import assess_asteroid_value
from datetime import datetime, timezone
from bson import ObjectId, Int64
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import random
from config.mongodb_config import missions_collection  # Import the missions collection
from enum import Enum


class MissionStatus(Enum):
    PLANNED = 0
    FUNDED = 1
    EXECUTING = 2
    SUCCESS = 3
    FAILED = 4


# Define the Pydantic model for the mission schema
class MinedElement(BaseModel):
    name: str
    mass_kg: Int64  # Use bson.Int64 for large mass values

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Mission(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")  # Generate a new ObjectId if not provided
    user_id: ObjectId  # Include user_id as an ObjectId
    asteroid_name: str
    success: bool = False  # Default to False if not provided
    distance: int = 0
    estimated_value: Int64 = Int64(0)  # Use bson.Int64 for large estimated values
    investment: int = 0
    total_cost: int = 0
    duration: int = 0
    status: MissionStatus = MissionStatus.PLANNED  # Default to PLANNED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mined_elements: List[MinedElement] = []  # Default to an empty list

    model_config = ConfigDict(arbitrary_types_allowed=True)


def get_missions(user_id: str) -> List[Mission]:
    """
    Get all missions for a given user ID from the MongoDB missions collection.

    Parameters:
    user_id (str): The user ID associated with the missions.

    Returns:
    List[Mission]: A list of Mission objects.
    """
    logging.info(f"Retrieving missions for user ID: {user_id}")
    try:
        user_id_obj = ObjectId(user_id)  # Convert user_id to ObjectId
    except Exception as e:
        logging.error(f"Invalid user_id format: {user_id}. Error: {e}")
        return []

    mission_documents = missions_collection.find({"user_id": user_id_obj})  # Query MongoDB for missions by user_id
    missions = [
        Mission(**{**mission, "status": MissionStatus(mission["status"])})
        for mission in mission_documents
    ]  # Convert each document to a Mission object
    logging.info(f"Retrieved {len(missions)} missions for user ID: {user_id}")
    return missions


def plan_mission(
    user_id: str,
    asteroid_name: str,
    ship_cost: int = 150_000_000,
    operational_cost_per_day: int = 50_000
) -> Mission:
    """
    Plan the entire mission and save it to the MongoDB missions collection.

    Parameters:
    user_id (str): The user ID planning the mission.
    asteroid_name (str): The name of the asteroid.
    ship_cost (int): The cost of the ship for the mission (default: $150,000,000).
    operational_cost_per_day (int): The operational cost per day for the mission (default: $50,000).

    Returns:
    Mission: A Pydantic Mission object representing the planned mission.
    """
    # Step 1: Locate the asteroid
    logging.info(f"Locating asteroid: {asteroid_name}")
    asteroid = find_by_full_name(asteroid_name)
    if not asteroid:
        logging.error(f"Asteroid '{asteroid_name}' not found.")
        return None

    # Step 2: Check for an existing ship
    logging.info("Checking for an existing ship.")
    ships = get_ships_by_user_id(user_id)
    if ships:
        logging.info(f"User already has a ship. Reducing ship cost to $90,000,000.")
        ship_cost = 90_000_000
    else:
        logging.info("No existing ship found. Using default ship cost of $150,000,000.")

    # Step 3: Calculate travel time
    travel_time = asteroid.get("moid_days", 1)  # Minimum Orbit Intersection Distance in days
    if travel_time == 0:
        travel_time = 1  # Default to 1 day if moid_days is zero
    travel_time = travel_time * 2  # Round trip
    travel_time += random.randint(1, 3)  # Add 1-3 days to establish the mining site

    # Step 4: Calculate total mission cost
    total_cost = ship_cost + (operational_cost_per_day * travel_time)
    logging.info(f"Total mission cost calculated: {total_cost}")

    # Step 5: Estimate potential reward
    estimated_value = Int64(assess_asteroid_value(asteroid))  # Convert to Int64
    logging.info(f"Estimated value of asteroid '{asteroid_name}': {estimated_value}")

    # Step 6: Create the mission object
    mission = Mission(
        user_id=ObjectId(user_id),  # Convert user_id to ObjectId
        asteroid_name=asteroid_name,
        distance=asteroid.get("distance", 0),
        estimated_value=estimated_value,
        investment=total_cost,  # Assume the investment matches the total cost
        total_cost=total_cost,
        duration=travel_time,
        status=MissionStatus.PLANNED,  # Use the enum
        created_at=datetime.now(timezone.utc),
        mined_elements=[]  # No elements mined yet
    )

    # Step 7: Save the mission to MongoDB
    mission_dict = mission.dict(by_alias=True)
    mission_dict["status"] = mission.status.value  # Convert enum to integer
    result = missions_collection.insert_one(mission_dict)
    mission.id = result.inserted_id

    logging.info(f"Mission planned successfully: {mission}")
    return mission


def fund_mission(mission_id, user_id, amount):
    """
    Temporarily does nothing while we build out funding logic.
    """
    pass


def execute_mission(mission_id):
    """
    This is where we will create/reuse ships
    """
    pass


if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example usage of plan_mission
    mission_plan = plan_mission(
        user_id="67e2a8cd282fa13f478eb5f6",
        asteroid_name="101955 Bennu (1999 RQ36)"
    )
    if mission_plan:
        logging.info(f"Mission plan saved: {mission_plan}")

    user_id = "67e2a8cd282fa13f478eb5f6"
    missions = get_missions(user_id)

    if missions:
        for mission in missions:
            print(f"Mission ID: {mission.id}, Asteroid: {mission.asteroid_name}, Status: {mission.status.name}")
    else:
        print("No missions found.")
