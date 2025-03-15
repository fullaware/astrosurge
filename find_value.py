import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
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
asteroids_collection = db['asteroids']

# Define the market values and their corresponding tickers
market_values = {
    'gold': 'GC=F',
    'silver': 'SI=F',
    'copper': 'HG=F',
    'platinum': 'PL=F',
    'palladium': 'PA=F'
}

# Fetch the current market value for each commodity
commodity_values = {}
for commodity, ticker in market_values.items():
    ticker_data = yf.Ticker(ticker)
    commodity_values[commodity] = ticker_data.history(period='1d')['Close'].iloc[0]

def assess_asteroid_value(full_name: str):
    """
    This function assesses the value of an asteroid based on its elements and their market values.
    It updates the asteroid's value in the MongoDB collection.

    Parameters:
    full_name (str): The full name of the asteroid.

    Returns:
    int: The total value of the asteroid, or None if the asteroid is not found.
    """
    asteroid = asteroids_collection.find_one({'full_name': full_name})
    if not asteroid:
        return None

    total_value = 0  # Initialize total_value
    for element in asteroid['elements']:
        element_name = element['name'].lower()
        mass_kg = element['mass_kg']
        # logging.info(f"{element_name}: {mass_kg} kg")
        if element_name in commodity_values:
            value = mass_kg * commodity_values[element_name]
            total_value += value

    # Ensure total_value does not exceed the maximum limit for 8-byte integers
    max_int_8_byte = 2**63 - 1
    if total_value > max_int_8_byte:
        total_value = max_int_8_byte

    total_value = round(total_value)  # Round the total value to the nearest whole number
    logging.info(f"Updating asteroid '{full_name}' with value: {total_value:,}")
    asteroids_collection.update_one({'_id': asteroid['_id']}, {'$set': {'value': total_value}})
    return total_value

def update_asteroids_without_value():
    """
    This function finds all asteroids in the MongoDB collection where the 'value' field does not exist,
    is 0, or is None. It assesses the value of each asteroid and updates the 'value' field.

    Returns:
    None
    """
    asteroids = asteroids_collection.find({'$or': [{'value': {'$exists': False}}, {'value': 0}, {'value': None}]})
    for asteroid in asteroids:
        full_name = asteroid['full_name']
        value = assess_asteroid_value(full_name)
        if value is not None:
            logging.info(f"Value of asteroid '{full_name}' updated successfully: {value:,}")
        else:
            logging.error(f"Asteroid '{full_name}' not found or market value not available.")

if __name__ == "__main__":
    update_asteroids_without_value()