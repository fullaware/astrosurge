import json
from config.mongodb_config import MongoDBConfig
from pprint import pprint
from bson import ObjectId, Int64  # Ensure you have pymongo installed
from datetime import datetime

def get_sample_document(collection_name):
    """
    Retrieve a sample document from a MongoDB collection.
    """
    collection = MongoDBConfig.get_collection(collection_name)
    document = collection.find_one()
    return document

def write_document_to_file(document, filename):
    """
    Write a document to a JSON file, converting ObjectId, datetime, and Int64 to string or int.
    """
    def convert_bson_types(obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to string
        if isinstance(obj, Int64):
            return int(obj)  # Convert Int64 to Python int
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO 8601 string
        if isinstance(obj, dict):
            return {key: convert_bson_types(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [convert_bson_types(item) for item in obj]
        return obj

    document = convert_bson_types(document)  # Convert BSON types to JSON-serializable types
    with open(filename, "w") as file:
        json.dump(document, file, indent=4)
    print(f"Document written to {filename}")

if __name__ == "__main__":
    collections = ["asteroids", "elements", "missions", "users", "ships"]
    for collection in collections:
        print(f"Fetching sample document from '{collection}'...")
        document = get_sample_document(collection)
        if document:
            pprint(document)
            filename = f"{collection[:-1]}.json"  # Remove the trailing 's' for singular filenames
            write_document_to_file(document, filename)
        else:
            print(f"No document found in collection '{collection}'.\n")