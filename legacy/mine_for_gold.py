import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import yfinance as yf
from amos.mine_asteroid import get_asteroid_by_name, mine_asteroid, update_asteroid

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from the environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collections
db = mongodb_client["asteroids"]  # Replace with your actual database name
mined_asteroids_collection = db["mined_asteroids"]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Convert price per ounce to price per kilogram (1 oz = 0.0283495 kg)
for commodity in commodity_values:
    commodity_values[commodity] = commodity_values[commodity] / 0.0283495

def mine_for_commodity(asteroid_name: str, uid: str, extraction_rate: int):
    """
    Mine the asteroid until one of the commodities is found and report the value.

    Parameters:
    asteroid_name (str): The name of the asteroid.
    uid (str): The user id.
    extraction_rate (int): The maximum extraction rate.

    Returns:
    None
    """
    asteroid = get_asteroid_by_name(asteroid_name)
    if not asteroid:
        logging.error(f"Asteroid {asteroid_name} not found.")
        return

    logging.info(f"Asteroid mass before mining: {asteroid['mass']} kg")

    while True:
        asteroid, total_elements_mined = mine_asteroid(asteroid, extraction_rate, uid)
        for element in total_elements_mined:
            element_name = element['name'].lower()
            if element_name in commodity_values:
                element_value = commodity_values[element_name] * element['mass_kg']
                logging.info(f"Found {element['mass_kg']} kg of {element_name} worth ${element_value:.2f}")
                update_asteroid(asteroid)
                return

        logging.info(f"Total elements mined: {sum([element['mass_kg'] for element in total_elements_mined])} kg")
        logging.info(f"Asteroid mass after mining: {asteroid['mass']} kg")

if __name__ == "__main__":
    asteroid_name = "101955 Bennu (1999 RQ36)"
    uid = "Brandon"
    extraction_rate = 1000  # Set the maximum extraction rate

    mine_for_commodity(asteroid_name, uid, extraction_rate)