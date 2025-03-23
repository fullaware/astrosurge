import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv('MONGODB_URI')

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client['asteroids']
collection = db['asteroids']

# List to store names that were updated
updated_names = []

# Counter for the number of updated documents
updated_count = 0

# Query all documents and update full_name with lstrip
for document in collection.find():
    full_name = document.get('full_name', '')
    stripped_full_name = full_name.lstrip()
    if full_name != stripped_full_name:
        collection.update_one({'_id': document['_id']}, {'$set': {'full_name': stripped_full_name}})
        updated_names.append(full_name)
        updated_count += 1

# Print all names where lstrip generated a change
print("Updated the following names with lstrip:")
for name in updated_names:
    print(name)

# Print the count of updated documents
print(f"Number of documents updated: {updated_count}")

print("Updated all documents with lstrip on full_name.")