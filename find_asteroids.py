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

def find_asteroids(min_distance_days, max_distance_days, num_asteroids):
    """
    Find asteroids within a specified range of minimum and maximum distance days.

    Parameters:
    min_distance_days (int): The minimum distance in days.
    max_distance_days (int): The maximum distance in days.
    num_asteroids (int): The number of random asteroids to return.

    Returns:
    tuple: A tuple containing the total count of matching asteroids and a list of randomly selected asteroids.
    """
    global collection  # Ensure collection is accessible within the function
    # Query to find asteroids where moid_days is between min_distance_days and max_distance_days
    query = {'moid_days': {'$gte': min_distance_days, '$lte': max_distance_days}}
    projection = {'full_name': 1, '_id': 0}
    try:
        # Get the total count of matching asteroids
        total_count = collection.count_documents(query)
        logging.info(f'Total count of matching asteroids: {total_count}')

        # Get all matching asteroids
        asteroids = list(collection.find(query, projection))
        logging.info('Query executed successfully')

        # Randomly select the specified number of asteroids from the list
        random_asteroids = random.sample(asteroids, min(num_asteroids, len(asteroids)))
        return total_count, random_asteroids
    except Exception as e:
        logging.error(f'Error executing query: {e}')
        return 0, []

# Automatically connect to MongoDB when the module is imported
connect_to_mongodb(MONGODB_URI)