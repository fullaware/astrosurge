import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid
import yfinance as yf

# Configure logging to show only ERROR level messages
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv('MONGODB_URI')

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client['asteroids']
ships_collection = db['ships']

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

def get_ship(name: str, uid: str):
    """
    Get or add a new ship to the ships collection. If a ship with the given name and uid already exists, return its oid.

    Parameters:
    name (str): The name of the ship.
    uid (str): The user id associated with the ship.

    Returns:
    dict: The newly created or existing ship document.
    """
    existing_ship = ships_collection.find_one({'name': name, 'uid': uid})
    if existing_ship:
        logging.info(f"Ship with name '{name}' and uid '{uid}' already exists: {existing_ship}")
        return existing_ship

    ship = {
        'oid': str(uuid.uuid4()),
        'name': name,
        'uid': uid,
        'shield': 100,
        'mining_power': 1000, # kg per hour
        'created': datetime.now(timezone.utc),
        'days_in_service': 0,
        'cargo': {}
    }
    ships_collection.insert_one(ship)
    logging.info(f"New ship added: {ship}")
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

def update_cargo(oid: str, elements_mined: list):
    """
    Update the cargo field for a ship with the mined elements.

    Parameters:
    oid (str): The object id of the ship.
    elements_mined (list): The list of mined elements.

    Returns:
    dict: The updated ship document.
    """
    ship = ships_collection.find_one({'oid': oid})
    if not ship:
        logging.error(f"Ship with oid {oid} not found.")
        return None

    cargo = ship.get('cargo', {})
    for element in elements_mined:
        element_name = element['name']
        mass_kg = element.get('mass_kg', 0)  # Use .get() to avoid KeyError
        if element_name in cargo:
            cargo[element_name] += mass_kg
        else:
            cargo[element_name] = mass_kg

    ships_collection.update_one({'oid': oid}, {'$set': {'cargo': cargo}})
    updated_ship = ships_collection.find_one({'oid': oid})
    logging.info(f"Updated ship cargo: {updated_ship}")
    return updated_ship

def list_cargo(oid: str):
    """
    List the elements in the cargo field of a ship and add a value field to each commodity.

    Parameters:
    oid (str): The object id of the ship.

    Returns:
    list: A list of elements in the cargo with their values.
    """
    ship = ships_collection.find_one({'oid': oid})
    if not ship:
        logging.error(f"Ship with oid {oid} not found.")
        return None

    cargo = ship.get('cargo', {})
    cargo_list = []
    for element_name, mass_kg in cargo.items():
        element_value = int(commodity_values.get(element_name.lower(), 0) * mass_kg)
        cargo_list.append({
            'name': element_name,
            'mass_kg': mass_kg,
            'value': element_value
        })

    logging.info(f"Cargo list for ship {oid}: {cargo_list}")
    return cargo_list

if __name__ == "__main__":
    # Example usage
    ship = get_ship("Merlin", "Brandon")
    updated_ship = update_days_in_service(ship['oid'])
    elements_mined = [
        {'name': 'Gold', 'mass_kg': 100},
        {'name': 'Silver', 'mass_kg': 200},
        {'name': 'Hydrogen', 'mass_kg': 300},
        {'name': 'Helium', 'mass_kg': 400}
    ]
    updated_ship = update_cargo(ship['oid'], elements_mined)
    cargo_list = list_cargo(ship['oid'])
    print(cargo_list)