import os
import logging
import random
from pymongo import MongoClient
from dotenv import load_dotenv

# Configure logging to show only ERROR level messages
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    logging.error('MONGODB_URI not found in environment variables')
    exit(1)

def connect_to_mongodb(uri):
    try:
        client = MongoClient(uri)
        db = client['asteroids']
        global collection
        collection = db['asteroids']
        logging.info('Connected to MongoDB')
    except Exception as e:
        logging.error(f'Error connecting to MongoDB: {e}')
        exit(1)

"""
find_asteroids.py
Retrieves asteroids by name or distance (moid_days).
"""

def find_by_name(name: str):
    """
    Find an asteroid by its name.

    Parameters:
    name (str): The name of the asteroid.

    Returns:
    dict: The asteroid data if found, otherwise None.
    """
    global collection
    query = {'full_name': name}
    projection = {'_id': 0}
    try:
        asteroid = collection.find_one(query, projection)
        return asteroid
    except Exception as e:
        logging.error(f'Error executing query: {e}')
        return None

def find_by_distance(max_days: float):
    """
    Find asteroids within a specified maximum distance in days.

    Parameters:
    max_days (float): The maximum distance in days.

    Returns:
    list: A list of asteroids within the specified distance.
    """
    global collection
    query = {'moid_days': {'$lte': max_days}}
    projection = {'full_name': 1, 'moid_days': 1, 'estimated_value': 1, '_id': 0}
    try:
        asteroids = list(collection.find(query, projection))
        return asteroids
    except Exception as e:
        logging.error(f'Error executing query: {e}')
        return []

# Automatically connect to MongoDB when the module is imported
connect_to_mongodb(MONGODB_URI)
