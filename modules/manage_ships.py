import yfinance as yf
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import ships_collection  # Import MongoDB configuration
from bson import ObjectId, Int64
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

def create_ship(name, user_id):
    """
    Create a new ship for the user.

    Parameters:
    name (str): The name of the ship.
    user_id (str): The ID of the user creating the ship.

    Returns:
    dict: The created ship document.
    """
    ship = {
        "name": name,
        "user_id": user_id,
        "shield": 100,
        "mining_power": 1000,
        "created": datetime.utcnow(),
        "days_in_service": 0,
        "location": 0,
        "mission": 0,
        "hull": 100,
        "cargo": [],  # Initialize as an empty array
        "capacity": 50000,
        "active": True,
    }
    ship_id = ships_collection.insert_one(ship).inserted_id
    return ships_collection.find_one({"_id": ship_id})

def get_ships_by_user_id(user_id: str) -> list:
    """
    Get all ships for a given user ID.

    Parameters:
    user_id (str): The user ID.

    Returns:
    list: A list of ship documents associated with the user.
    """
    ships = ships_collection.find({"user_id": user_id})  # Retrieve all ships for the user
    ships_list = list(ships)  # Convert the cursor to a list
    if not ships_list:
        logging.error(f"No ships found for user ID '{user_id}'.")
    else:
        logging.info(f"Found {len(ships_list)} ship(s) for user ID '{user_id}'.")
    return ships_list

def update_ship(ship_id: ObjectId, cargo_list: list):
    """
    Update the ship's cargo by incrementing the mass of existing elements or adding new ones.

    Parameters:
    ship_id (ObjectId): The ship ID.
    cargo_list (list): A list of cargo items to update, where each item is a dictionary with 'name' and 'mass_kg'.

    Returns:
    dict: The updated ship document.
    """
    for item in cargo_list:
        # Validate that the item is a dictionary
        if not isinstance(item, dict):
            logging.warning(f"Invalid cargo item (not a dictionary): {item}")
            continue

        # Extract name and mass_kg with validation
        name = item.get("name")
        mass_kg = item.get("mass_kg", 0)

        if not name or not isinstance(mass_kg, (int, float)) or mass_kg <= 0:
            logging.warning(f"Invalid cargo item: {item}")
            continue

        # Increment the mass of the existing cargo item or add it if it doesn't exist
        ships_collection.update_one(
            {"_id": ship_id, "cargo.name": name},  # Match the ship and the specific cargo item
            {"$inc": {"cargo.$.mass_kg": mass_kg}}  # Increment the mass of the existing item
        )

        # If the item doesn't exist, add it to the cargo array
        ships_collection.update_one(
            {"_id": ship_id, "cargo.name": {"$ne": name}},  # Ensure the item doesn't already exist
            {"$push": {"cargo": {"name": name, "mass_kg": mass_kg}}}  # Add the new item
        )

    updated_ship = ships_collection.find_one({"_id": ship_id})
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
    Update the ship's cargo by incrementing the mass of existing elements or adding new ones.

    Parameters:
    ship_id (ObjectId): The ship ID.
    cargo_list (list): A list of cargo items to update, where each item is a dictionary with 'name' and 'mass_kg'.

    Returns:
    None
    """
    for item in cargo_list:
        name = item.get("name")
        mass_kg = item.get("mass_kg", 0)

        if not name or mass_kg <= 0:
            logging.warning(f"Invalid cargo item: {item}")
            continue

        # Increment the mass of the existing cargo item or add it if it doesn't exist
        ships_collection.update_one(
            {"_id": ship_id, "cargo.name": name},  # Match the ship and the specific cargo item
            {"$inc": {"cargo.$.mass_kg": mass_kg}},  # Increment the mass of the existing item
        )

        # If the item doesn't exist, add it to the cargo array
        ships_collection.update_one(
            {"_id": ship_id, "cargo.name": {"$ne": name}},  # Ensure the item doesn't already exist
            {"$push": {"cargo": {"name": name, "mass_kg": mass_kg}}},  # Add the new item
        )

    logging.info(f"Cargo updated for ship ID '{ship_id}'.")

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

def repair_ship(ship_id: ObjectId) -> Int64:
    """
    Repair the ship and calculate the cost based on the hull damage.

    Parameters:
    ship_id (ObjectId): The ship ID.

    Returns:
    Int64: The cost to repair the ship.
    """
    # Retrieve the ship's current hull value
    ship = ships_collection.find_one({"_id": ship_id})
    if not ship:
        logging.error(f"Ship ID '{ship_id}' not found.")
        return Int64(0)

    current_hull = ship.get("hull", 100)
    if current_hull >= 100:
        logging.info(f"Ship ID '{ship_id}' is already fully repaired.")
        return Int64(0)

    # Calculate the cost to repair the ship
    hull_damage = 100 - current_hull
    min_cost = hull_damage * 250_000
    max_cost = hull_damage * 1_000_000

    # Repair the ship
    ships_collection.update_one(
        {"_id": ship_id},
        {"$set": {"hull": 100, "shield": 100, "active": True}},
        upsert=True
    )
    logging.info(f"Ship ID '{ship_id}' repaired. Hull restored to 100.")

    # Return the repair cost as an Int64
    repair_cost = Int64((min_cost + max_cost) // 2)  # Average cost
    logging.info(f"Repair cost for ship ID '{ship_id}': {repair_cost}")
    return repair_cost

def get_ship(ship_id: ObjectId) -> dict:
    """
    Retrieve a single ship by its ID.

    Parameters:
    ship_id (ObjectId): The ship ID.

    Returns:
    dict: The ship document if found, otherwise None.
    """
    ship = ships_collection.find_one({"_id": ship_id})
    if not ship:
        logging.error(f"Ship ID '{ship_id}' not found.")
        return None
    logging.info(f"Retrieved ship: {ship}")
    return ship

def update_ship_attributes(ship_id: ObjectId, updates: dict):
    """
    Update attributes of a selected ship.
    """

    if updates:
        ships_collection.update_one({"_id": ship_id}, {"$set": updates})
        print(f"Updated ship: {ships_collection.find_one({'_id': ship_id})}")
    else:
        print("No updates were made.")

if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example usage of create_ship
    new_ship = create_ship("Waffle", "Brandon")
    logging.info(f"New ship: {new_ship}")

    # Example usage of get_ships_by_user_id
    ships = get_ships_by_user_id("Brandon")
    logging.info(f"Ships: {ships}")

    # Example usage of get_ship
    if ships:
        ship_id = ships[0]["_id"]
        ship = get_ship(ship_id)
        if ship:
            logging.info(f"Retrieved ship: {ship}")

            # Example: Check and update ship status
            if ship["hull"] <= 0:
                ships_collection.update_one(
                    {"_id": ship_id},
                    {"$set": {"active": False}}
                )
                logging.info(f"Ship ID '{ship_id}' status updated to 'inactive'.")
            else:
                logging.info(f"Ship ID '{ship_id}' is active with hull: {ship['hull']}.")