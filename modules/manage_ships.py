import yfinance as yf
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import ships_collection  # Import MongoDB configuration
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, conint

# Define the market values and their corresponding tickers or custom values
market_values = {
    'gold': 'GC=F',
    'silver': 'SI=F',
    'copper': 'HG=F',
    'platinum': 'PL=F',
    'palladium': 'PA=F',
    'hydrogen': 10,  # Custom market value in $ per kg
    'helium': 15     # Custom market value in $ per kg
}

# Fetch the current market value for each commodity
commodity_values = {}
for commodity, ticker_or_value in market_values.items():
    if isinstance(ticker_or_value, str):
        ticker_data = yf.Ticker(ticker_or_value)
        history = ticker_data.history(period='7d')
        if not history.empty:
            commodity_values[commodity] = history['Close'].iloc[0] / 0.0283495  # Convert from $/oz to $/kg
        else:
            logging.error(f"{ticker_or_value}: possibly delisted; no price data found (period='7d')")
            commodity_values[commodity] = 0  # Set a default value or handle as needed
    else:
        # Use custom market values for elements without tickers
        commodity_values[commodity] = ticker_or_value

class CargoItem(BaseModel):
    name: str
    mass_kg: conint(ge=0)  # ensures mass_kg is an integer ≥ 0

def create_ship(name: str, user_id: str) -> dict:
    """
    Create a new ship with the given name and associate it with the user ID.

    Parameters:
    name (str): The name of the ship.
    user_id (str): The user ID.

    Returns:
    dict: The created ship document or the existing ship document if it already exists.
    """
    existing_ship = ships_collection.find_one({"name": name, "user_id": user_id})
    if existing_ship:
        logging.info(f"Ship with name '{name}' and user ID '{user_id}' already exists: {existing_ship}")
        return existing_ship

    new_ship = {
        "_id": ObjectId(),
        "name": name,
        "user_id": user_id,
        "shield": 100,
        "mining_power": 1000,
        "created": datetime.now(),
        "days_in_service": 0,
        "location": 0,
        "mission": 0,
        "hull": 100,
        "cargo": {},
        "capacity": 50000,
        "active": True  # New active field
    }
    ships_collection.insert_one(new_ship)
    logging.info(f"New ship created: {new_ship}")
    return new_ship

def get_ship_by_user_id(user_id: str) -> dict:
    """
    Get the ship for a given user ID.

    Parameters:
    user_id (str): The user ID.

    Returns:
    dict: The ship document.
    """
    ship = ships_collection.find_one({"user_id": user_id})
    if not ship:
        logging.error(f"Ship for user ID '{user_id}' not found.")
        return {}
    return ship

def update_ship(ship_id: ObjectId, updates: dict) -> dict:
    """
    Update the attributes of a ship.

    Parameters:
    ship_id (ObjectId): The ship ID.
    updates (dict): The dictionary of attributes to update.

    Returns:
    dict: The updated ship document.
    """
    ships_collection.update_one(
        {"_id": ship_id},
        {"$set": updates},
        upsert=True
    )
    updated_ship = ships_collection.find_one({"_id": ship_id})
    logging.info(f"Ship updated: {updated_ship}")
    return updated_ship

def update_days_in_service(ship_id: ObjectId) -> dict:
    """
    Update the days in service for a ship by incrementing it by 1 day.

    Parameters:
    ship_id (ObjectId): The ship ID.

    Returns:
    dict: The updated ship document.
    """
    ship = ships_collection.find_one({'_id': ship_id})
    if not ship:
        logging.error(f"Ship with ID {ship_id} not found.")
        return None

    new_days_in_service = ship['days_in_service'] + 1
    ships_collection.update_one({'_id': ship_id}, {'$set': {'days_in_service': new_days_in_service}})
    updated_ship = ships_collection.find_one({'_id': ship_id})
    logging.info(f"Updated ship: {updated_ship}")
    return updated_ship

def normalize_cargo(cargo_list: list) -> list:
    """
    Ensure that all cargo items have 'mass_kg' as a Python int.
    """
    for item in cargo_list:
        if "mass_kg" in item:
            item["mass_kg"] = int(item["mass_kg"])
    return cargo_list

def update_cargo(ship_id: ObjectId, cargo_list: list):
    """
    Update the ship's cargo with validated data.
    """
    filtered_cargo = [item for item in cargo_list if "mass_kg" in item]
    validated_cargo = [CargoItem(**item).dict() for item in filtered_cargo]
    # Store validated_cargo in the database, ensuring mass_kg is Int64
    
    # Example:
    # For each item, convert mass_kg to int/bson.Int64 if needed
    # Then update ship record in the DB with the new cargo
    # ...

def list_cargo(ship_id: ObjectId) -> list:
    """
    Retrieve the ship's cargo from the database and parse it as CargoItem.
    """
    cargo_data = []  # Retrieve raw cargo data from DB
    # Convert each item to a CargoItem, then to dict:
    validated_cargo = [CargoItem(**item).dict() for item in cargo_data]
    return validated_cargo

def empty_cargo(ship_id: ObjectId):
    """
    Empty the cargo of a ship.

    Parameters:
    ship_id (ObjectId): The ship ID.

    Returns:
    None
    """
    ships_collection.update_one(
        {"_id": ship_id},
        {"$set": {"cargo": []}},
        upsert=True
    )
    logging.info(f"Cargo emptied for ship ID '{ship_id}'.")

def repair_ship(ship_id: ObjectId):
    """
    Repair the ship.

    Parameters:
    ship_id (ObjectId): The ship ID.

    Returns:
    None
    """
    ships_collection.update_one(
        {"_id": ship_id},
        {"$set": {"hull": 100, "shield": 100, "active": True}},
        upsert=True
    )
    logging.info(f"Ship ID '{ship_id}' repaired.")

def check_ship_status(ship_id: ObjectId):
    """
    Check the status of a ship and update it to 'inactive' if the hull is 0.

    Parameters:
    ship_id (ObjectId): The ship ID.

    Returns:
    None
    """
    ship = ships_collection.find_one({"_id": ship_id})
    if not ship:
        logging.error(f"Ship ID '{ship_id}' not found.")
        return

    if ship["hull"] <= 0:
        ships_collection.update_one(
            {"_id": ship_id},
            {"$set": {"active": False}}
        )
        logging.info(f"Ship ID '{ship_id}' status updated to 'inactive'.")

if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example usage of create_ship
    new_ship = create_ship("Waffle", "Brandon")
    logging.info(f"New ship: {new_ship}")

    # Example usage of get_ship_by_user_id
    ship = get_ship_by_user_id("Brandon")
    logging.info(f"Ship: {ship}")

    # Example usage of update_ship
    updated_ship = update_ship(ship["_id"], {"location": 1, "shield": 90, "days_in_service": 1, "mission": 1, "hull": 95})
    logging.info(f"Updated ship: {updated_ship}")

    # Example usage of update_cargo
    update_cargo(ship["_id"], [{"name": "Gold", "mass_kg": 100}])

    # Example usage of list_cargo
    cargo = list_cargo(ship["_id"])
    logging.info(f"Cargo: {cargo}")

    # Example usage of empty_cargo
    empty_cargo(ship["_id"])

    # Example usage of repair_ship
    repair_ship(ship["_id"])

    # Example usage of check_ship_status
    check_ship_status(ship["_id"])