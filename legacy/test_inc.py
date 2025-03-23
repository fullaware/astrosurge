import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.int64 import Int64
import pprint

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection URI from environment variables
mongodb_uri = os.getenv("MONGODB_URI")
if not mongodb_uri:
    raise ValueError("MONGODB_URI environment variable is not set")

# Connect to MongoDB
client = MongoClient(mongodb_uri)
db = client.test  # Connect to 'test' database
collection = db.test  # Connect to 'test' collection

# Create a document with NumberLong value
doc = {"nlong": Int64("999999999999999999")}  # Int64 maps to NumberLong in MongoDB

# Insert the document
result = collection.insert_one(doc)
doc_id = result.inserted_id

print(f"Inserted document with ID: {doc_id}")
original_doc = collection.find_one({"_id": doc_id})
print("Original document:")
pprint.pprint(original_doc)

# Update the document to increment the NumberLong value by 1
update_result = collection.update_one(
    {"_id": doc_id},  # Filter by the document ID
    {"$inc": {"nlong": 1}}  # Increment nlong field by 1
)

# Fetch the updated document
updated_doc = collection.find_one({"_id": doc_id})
print("\nUpdated document:")
pprint.pprint(updated_doc)

# Verify the update
print(f"\nUpdated {update_result.modified_count} document")
print(f"NumberLong value incremented from 999999999999999 to {updated_doc['nlong']}")

# Close the MongoDB connection
client.close()