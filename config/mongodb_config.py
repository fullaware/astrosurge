from pymongo import MongoClient
from dotenv import load_dotenv
import os

class MongoDBConfig:
    """
    MongoDB Configuration class to manage database connections and collections.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get MongoDB URI from environment variables
    MONGODB_URI = os.getenv("MONGODB_URI")

    # Initialize MongoDB client
    _client = MongoClient(MONGODB_URI)

    # Specify the database
    _db = _client["asteroids"]  # Replace with your actual database name

    @staticmethod
    def get_collection(collection_name: str):
        """
        Get a MongoDB collection by name.

        Parameters:
        collection_name (str): The name of the collection.

        Returns:
        Collection: The MongoDB collection object.
        """
        return MongoDBConfig._db[collection_name]

    @staticmethod
    def get_database():
        """
        Get the MongoDB database object.

        Returns:
        Database: The MongoDB database object.
        """
        return MongoDBConfig._db