import os
from pymongo import MongoClient
from dotenv import load_dotenv
import yfinance as yf
from pprint import pprint

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
    asteroid = asteroids_collection.find_one({'full_name': full_name})
    if not asteroid:
        return None

    total_value = 0  # Initialize total_value
    for element in asteroid['elements']:
        element_name = element['name'].lower()
        mass_kg = element['mass_kg']
        print(f"{element_name}: {mass_kg} kg")
        if element_name in commodity_values:
            value = mass_kg * commodity_values[element_name]
            total_value += value

    # Ensure total_value does not exceed the maximum limit for 8-byte integers
    max_int_8_byte = 2**63 - 1
    if total_value > max_int_8_byte:
        total_value = max_int_8_byte

    total_value = round(total_value)  # Round the total value to the nearest whole number
    asteroids_collection.update_one({'_id': asteroid['_id']}, {'$set': {'value': total_value}})
    return total_value

if __name__ == "__main__":
    full_name = "1221 Amor (1932 EA1)"
    value = assess_asteroid_value(full_name)
    if value is not None:
        print(f"Value of asteroid '{full_name}' updated successfully: {value:,}")
    else:
        print(f"Asteroid '{full_name}' not found or market value not available.")