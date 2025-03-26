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
from modules.manage_ships import create_ship, update_cargo, list_cargo, empty_cargo, repair_ship, get_ships_by_user_id
from modules.find_asteroids import find_by_full_name, find_by_distance
from modules.find_value import assess_asteroid_value
from modules.mine_asteroid import mine_hourly, update_mined_asteroid
from modules.manage_elements import find_elements_use, sell_elements
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
import random


# Define the Pydantic model for the mission schema
class MinedElement(BaseModel):
    name: str
    mass_kg: int


class Mission(BaseModel):
    asteroid_name: str
    distance: int
    estimated_value: int
    investment: int
    total_cost: int
    duration: int
    status: int
    created_at: datetime
    mined_elements: List[MinedElement]
    success: bool


def get_missions(user_id: str) -> List[Mission]:
    """
    Get all missions for a given user id.

    Parameters:
    user_id (str): The user id associated with the missions.

    Returns:
    list: A list of mission documents.
    """
    # Placeholder for mission retrieval logic
    missions = []  # Replace with actual mission retrieval logic
    return [Mission(**mission) for mission in missions]


def plan_mission(
    user_id: str,
    asteroid_name: str,
    ship_cost: int = 150_000_000,
    operational_cost_per_day: int = 50_000
) -> Mission:
    """
    Plan the entire mission:
    1) Where are we going? (find_asteroids)
    2) How are we getting there? (ship.cost)
    3) How long will it take? (asteroid.moid_days; if zero, travel time is 1 day + 1-3 days to establish mining site)
    4) How much will it cost? (ship.cost + operational costs per day * days)
    5) How much will we make? (find_value - costs)

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
    travel_time += random.randint(1, 3)  # Add 1-3 days to establish the mining site

    # Step 4: Calculate total mission cost
    total_cost = ship_cost + (operational_cost_per_day * travel_time)
    logging.info(f"Total mission cost calculated: {total_cost}")

    # Step 5: Estimate potential reward
    estimated_value = assess_asteroid_value(asteroid)
    logging.info(f"Estimated value of asteroid '{asteroid_name}': {estimated_value}")

    # Step 6: Create the mission object
    mission = Mission(
        asteroid_name=asteroid_name,
        distance=asteroid.get("distance", 0),
        estimated_value=estimated_value,
        investment=total_cost,  # Assume the investment matches the total cost
        total_cost=total_cost,
        duration=travel_time,
        status=1,  # Status 1 indicates "planned"
        created_at=datetime.now(timezone.utc),
        mined_elements=[],  # No elements mined yet
        success=False  # Mission not yet executed
    )

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
        user_id="example_user_id",
        asteroid_name="101955 Bennu (1999 RQ36)"
    )
    if mission_plan:
        logging.info(f"Mission plan: {mission_plan}")
