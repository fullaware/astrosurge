"""
manage_ships.py

This module is responsible for managing all Create, Read, Update, and Delete (CRUD) operations for documents in the `asteroids.ships` collection. It provides functionality to interact with ship data stored in the database, ensuring that all operations related to ships are centralized and consistent.

### Goals and Expectations:

1. **Ship Creation**:
   - Allow users to create new ships with default attributes such as `name`, `capacity`, `hull`, and `location`.
   - Ensure that ships are associated with a specific user (`user_id`).

2. **Ship Retrieval**:
   - Provide methods to retrieve all ships for a given user (`get_ships_by_user_id`).
   - Allow retrieval of a single ship by its unique ID (`get_ship`).
   - Support listing and viewing ship details, including cargo and status.

3. **Ship Updates**:
   - Enable updates to ship attributes such as `hull`, `location`, `shield`, and `active` status.
   - Provide functionality to manage ship cargo, including adding, updating, and removing cargo items.
   - Support operations to repair ships and calculate repair costs based on hull damage.

4. **Cargo Management**:
   - Allow ships to store and manage cargo items, including tracking the total mass of cargo.
   - Provide methods to normalize, list, and empty cargo for a specific ship.

5. **Utility Functions**:
   - Include helper functions to calculate the current cargo mass, normalize cargo data, and validate cargo items.
   - Ensure that all operations are logged for debugging and auditing purposes.

### Key Features:
- Centralized management of ship-related data to ensure consistency across the application.
- Integration with MongoDB for persistent storage of ship documents.
- Logging of all operations to facilitate debugging and monitoring.

This module is designed to be reusable and extensible, allowing for future enhancements such as advanced ship customization or integration with other modules (e.g., missions, mining operations).
"""

from config.logging_config import logging  # Updated logging import
from config.mongodb_config import MongoDBConfig  # Updated MongoDBConfig import
from bson import ObjectId, Int64
from datetime import datetime
from pydantic import BaseModel, conint
from models import ShipModel

# Use MongoDBConfig to get the ships collection
ships_collection = MongoDBConfig.get_collection("ships")


class CargoItem(BaseModel):
    name: str
    mass_kg: conint(ge=0)  # ensures mass_kg is an integer ≥ 0

def create_ship(name: str, user_id: ObjectId) -> dict:
    """
    Create a new ship for the user.

    Parameters:
    name (str): The name of the ship.
    user_id (ObjectId): The ID of the user creating the ship.

    Returns:
    dict: The created ship document.
    """
    logging.info(f"Creating ship '{name}' for user_id: {user_id}")
    ship = {
        "name": name,
        "user_id": user_id,
        "hull": 100,
        "cargo": [],
        "capacity": 50000,
        "created_at": datetime.utcnow(),
    }
    ship_id = ships_collection.insert_one(ship).inserted_id
    logging.info(f"Ship '{name}' created with ID: {ship_id}")
    return ships_collection.find_one({"_id": ship_id})

def get_ships_by_user_id(user_id: ObjectId) -> list:
    """
    Get all ships for a given user ID.

    Parameters:
    user_id (ObjectId): The user ID.

    Returns:
    list: A list of ship documents associated with the user.
    """
    logging.info(f"Retrieving ships for user_id: {user_id}")
    ships = list(ships_collection.find({"user_id": user_id}))
    logging.info(f"Retrieved {len(ships)} ships for user_id: {user_id}")
    return ships

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
    Retrieve the ship's cargo from the database.

    Parameters:
    ship_id (ObjectId): The ship ID.

    Returns:
    list: A list of cargo items, or an empty list if no cargo is found.
    """
    # Retrieve the ship document from the database
    ship = ships_collection.find_one({"_id": ship_id}, {"cargo": 1})  # Only fetch the 'cargo' field
    if not ship or "cargo" not in ship:
        logging.warning(f"No cargo found for ship ID '{ship_id}'.")
        return []

    # Return the cargo list
    cargo_data = ship["cargo"]
    logging.info(f"Cargo retrieved for ship ID '{ship_id}': {cargo_data}")
    return cargo_data

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

def update_ship_cargo(ship_id: ObjectId, cargo_list: list):
    """
    Updates the cargo of a ship in the database.

    Parameters:
    ship_id (ObjectId): The ID of the ship.
    cargo_list (list): A list of cargo items to add or update.

    Returns:
    None
    """
    for item in cargo_list:
        name = item.get("name")
        mass_kg = item.get("mass_kg", 0)

        # Convert mass_kg to Int64
        mass_kg = Int64(mass_kg)

        if not name or mass_kg <= 0:
            logging.warning(f"Invalid cargo item: {item}. Skipping.")
            continue

        # Increment the mass of the existing cargo item or add it if it doesn't exist
        result = ships_collection.update_one(
            {"_id": ship_id, "cargo.name": name},  # Match the ship and the specific cargo item
            {"$inc": {"cargo.$.mass_kg": mass_kg}},  # Increment the mass of the existing item
        )

        # If the item doesn't exist, add it to the cargo array
        if result.matched_count == 0:
            ships_collection.update_one(
                {"_id": ship_id},  # Match the ship
                {"$push": {"cargo": {"name": name, "mass_kg": mass_kg}}},  # Add the new item
            )

    logging.info(f"Cargo updated for ship ID '{ship_id}'.")

def get_current_cargo_mass(ship_id: ObjectId) -> int:
    """
    Calculate the current cargo mass of a ship.

    Parameters:
    ship_id (ObjectId): The ID of the ship.

    Returns:
    int: The total mass of the cargo in kilograms.
    """
    ship = get_ship(ship_id)  # Retrieve the ship document
    if not ship or 'cargo' not in ship:
        return 0  # Return 0 if the ship or cargo is missing

    # Sum up the mass of all cargo items
    return sum(item.get('mass_kg', 0) for item in ship['cargo'])

def find_ship_by_id(ship_id: str) -> ShipModel:
    """
    Find a ship by its ID and validate it against the Pydantic model.
    """
    ship = ships_collection.find_one({"_id": ship_id})
    if ship:
        return ShipModel(**ship)
    return None

def list_ships_by_user(user_id: str):
    """
    List all ships for a specific user.
    """
    ships = ships_collection.find({"user_id": user_id})
    return [ShipModel(**ship) for ship in ships]


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