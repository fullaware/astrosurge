import os
import random
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid
import yfinance as yf
from logging_config import logging  # Import logging configuration
from mongodb_config import ships_collection  # Import MongoDB configuration
from bson import Int64  # Import Int64 from bson

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv('MONGODB_URI')

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client['asteroids']
users_collection = db['users']

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

def get_ship(uid: str) -> dict:
    """
    Get the ship for a given user ID.

    Parameters:
    uid (str): The user ID.

    Returns:
    dict: The ship document.
    """
    ship = ships_collection.find_one({"uid": uid})
    if not ship:
        logging.error(f"Ship for user ID '{uid}' not found.")
        return {}
    return ship

def update_days_in_service(oid: str):
    """
    Update the days in service for a ship by incrementing it by 1 day.

    Parameters:
    oid (str): The object id of the ship.

    Returns:
    dict: The updated ship document.
    """
    ship = ships_collection.find_one({'oid': oid})
    if not ship:
        logging.error(f"Ship with oid {oid} not found.")
        return None

    new_days_in_service = ship['days_in_service'] + 1
    ships_collection.update_one({'oid': oid}, {'$set': {'days_in_service': new_days_in_service}})
    updated_ship = ships_collection.find_one({'oid': oid})
    logging.info(f"Updated ship: {updated_ship}")
    return updated_ship

def update_cargo(ship_id: str, cargo: list):
    """
    Update the cargo of a ship.

    Parameters:
    ship_id (str): The ship ID.
    cargo (list): The list of cargo items to update.

    Returns:
    None
    """
    ships_collection.update_one(
        {"_id": ship_id},
        {"$set": {"cargo": cargo}},
        upsert=True
    )
    logging.info(f"Cargo updated for ship ID '{ship_id}'.")

def list_cargo(ship_id: str) -> list:
    """
    List the cargo of a ship.

    Parameters:
    ship_id (str): The ship ID.

    Returns:
    list: The list of cargo items.
    """
    ship = ships_collection.find_one({"_id": ship_id})
    if not ship:
        logging.error(f"Ship ID '{ship_id}' not found.")
        return []
    return ship.get("cargo", [])

def empty_cargo(ship_id: str):
    """
    Empty the cargo of a ship.

    Parameters:
    ship_id (str): The ship ID.

    Returns:
    None
    """
    ships_collection.update_one(
        {"_id": ship_id},
        {"$set": {"cargo": []}},
        upsert=True
    )
    logging.info(f"Cargo emptied for ship ID '{ship_id}'.")

def repair_ship(ship_id: str):
    """
    Repair the ship.

    Parameters:
    ship_id (str): The ship ID.

    Returns:
    None
    """
    ships_collection.update_one(
        {"_id": ship_id},
        {"$set": {"hull": 100, "shield": 100}},
        upsert=True
    )
    logging.info(f"Ship ID '{ship_id}' repaired.")

if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example usage of get_ship
    ship = get_ship("example_uid")
    logging.info(f"Ship: {ship}")

    # Example usage of update_cargo
    update_cargo("example_ship_id", [{"name": "Gold", "mass_kg": 100}])

    # Example usage of list_cargo
    cargo = list_cargo("example_ship_id")
    logging.info(f"Cargo: {cargo}")

    # Example usage of empty_cargo
    empty_cargo("example_ship_id")

    # Example usage of repair_ship
    repair_ship("example_ship_id")