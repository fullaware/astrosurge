import pymongo
from bson import ObjectId
from datetime import datetime, UTC
import logging
import re
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models.models import MissionModel, AsteroidElementModel, MissionDay, ShipModel, PyInt64, User
from config import MongoDBConfig, LoggingConfig
from amos.mine_asteroid import fetch_market_prices, simulate_travel_day, simulate_mining_day, HOURS_PER_DAY, calculate_confidence
from amos.event_processor import EventProcessor

db = MongoDBConfig.get_database()
LoggingConfig.setup_logging(log_to_file=False)

COMMODITIES = ["Copper", "Silver", "Palladium", "Platinum", "Gold"]
VALIDATION_PATTERN = re.compile(r'^[a-zA-Z0-9 ]{1,30}$')

def validate_ship_name(ship_name: str) -> bool:
    return bool(VALIDATION_PATTERN.match(ship_name))

def create_new_ship(user_id: str, ship_name: str, username: str, company_name: str) -> ShipModel:
    if not validate_ship_name(ship_name):
        raise ValueError(f"Ship name '{ship_name}' must be alphanumeric and up to 30 characters")
    ship_data = {
        "_id": ObjectId(),
        "name": ship_name,
        "user_id": user_id,
        "shield": 100,
        "mining_power": 500,
        "created": datetime.now(UTC),
        "days_in_service": 0,
        "location": PyInt64(0),
        "mission": 0,
        "hull": 100,
        "cargo": [],
        "capacity": 50000,
        "active": True,
        "missions": [],
        "destroyed": False
    }
    db.ships.insert_one(ship_data)
    logging.info(f"User {username}: Created new ship {ship_name} for company {company_name}")
    return ShipModel(**ship_data)

def get_day(summary) -> int:
    return summary.day if isinstance(summary, MissionDay) else summary["day"]

def get_elements_mined(summary) -> dict:
    elements = summary.elements_mined if isinstance(summary, MissionDay) else summary.get("elements_mined")
    return elements if elements is not None else {}

def get_daily_value(summary) -> int:
    value = summary.daily_value if isinstance(summary, MissionDay) else summary.get("daily_value", 0)
    return value if value is not None else 0

def process_single_mission(mission_raw: dict, day: int = None, api_event: dict = None, username: str = None, company_name: str = None) -> dict:
    """
    Process a single mission using SimPy-based simulation.
    
    This is a wrapper around the SimPy-based mission simulator.
    """
    mission_id = str(mission_raw["_id"])
    
    try:
        from amos.mission_simulator import simulate_mission
        return simulate_mission(mission_raw, day, api_event, username, company_name)
    except Exception as e:
        logging.error(f"User {username}: Failed to simulate mission {mission_id}: {e}")
        return {"error": f"Simulation error: {str(e)}"}

def mine_asteroid(user_id: str, day: int = None, api_event: dict = None, username: str = None, company_name: str = None) -> dict:
    try:
        active_missions = list(db.missions.find({"user_id": user_id, "status": 0}))
    except pymongo.errors.AutoReconnect as e:
        logging.error(f"User {username}: Failed to fetch active missions for user {user_id}: {e}")
        return {"error": "Trouble accessing the database, please try again later"}
    
    if not active_missions:
        logging.info(f"User {username}: No active missions found for user {user_id}")
        return {"message": "No active missions to process"}

    results = {}
    for mission_raw in active_missions:
        mission_id = str(mission_raw["_id"])
        result = process_single_mission(mission_raw, day, api_event, username, company_name)
        results[mission_id] = result
    return results

if __name__ == "__main__":
    user_id = "some_user_id"
    mine_asteroid(user_id)