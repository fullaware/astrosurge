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

from config.logging_config import logging  # Updated logging import
from config.mongodb_config import MongoDBConfig 
from models import MissionModel
from bson import ObjectId, Int64
from enum import Enum

# Use MongoDBConfig to get the missions collection
missions_collection = MongoDBConfig.get_collection("missions")

class MissionStatus(Enum):
    PLANNED = 0
    FUNDED = 1
    EXECUTING = 2
    SUCCESS = 3
    FAILED = 4

def get_missions(user_id: ObjectId, filter: dict = None):
    logging.info(f"Retrieving missions for user_id: {user_id}")
    filter = filter or {}
    filter["user_id"] = user_id

    raw_missions = missions_collection.find(filter)
    missions = []
    for mission in raw_missions:
        mission["status"] = MissionStatus(mission["status"])
        missions.append(MissionModel(**mission))
    logging.info(f"Retrieved {len(missions)} missions for user_id: {user_id}")
    return missions

def update_mission(mission_id: ObjectId, updates: dict):
    logging.info(f"Updating mission {mission_id} with updates: {updates}")
    if "status" in updates and isinstance(updates["status"], MissionStatus):
        updates["status"] = updates["status"].value

    result = missions_collection.update_one({"_id": mission_id}, {"$set": updates})
    if result.modified_count > 0:
        logging.info(f"Mission {mission_id} updated successfully.")
    else:
        logging.warning(f"No changes made to mission {mission_id}.")

def find_mission_by_id(mission_id: str) -> MissionModel:
    """
    Find a mission by its ID and validate it against the Pydantic model.
    """
    mission = missions_collection.find_one({"_id": mission_id})
    if mission:
        return MissionModel(**mission)
    return None

def list_missions_by_user(user_id: str):
    """
    List all missions for a specific user.
    """
    missions = missions_collection.find({"user_id": user_id})
    return [MissionModel(**mission) for mission in missions]
