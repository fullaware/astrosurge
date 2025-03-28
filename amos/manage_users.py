from werkzeug.security import generate_password_hash, check_password_hash
from amos.find_value import assess_element_values, commodity_values  # Update the import path for find_value
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import users_collection  # Import MongoDB configuration
from bson import Int64, ObjectId  # Import Int64 and ObjectId from bson
from datetime import datetime  # Import datetime for timestamp

def update_users(user_id: ObjectId, elements: list):
    """
    Update the users collection with the mined elements and increment the mined value.

    Parameters:
    user_id (ObjectId): The user ID.
    elements (list): The list of elements mined.
    """
    try:
        total_mined_mass = sum(element["mass_kg"] for element in elements)
        total_value = Int64(0)

        # Update the users collection and calculate the total value
        for element in elements:
            element_value = assess_element_values([element], commodity_values)
            total_value += element_value
            users_collection.update_one(
                {"_id": user_id},
                {"$inc": {f"elements.{element['name']}.mass_kg": Int64(element["mass_kg"]),
                          f"elements.{element['name']}.value": Int64(element_value)}},
                upsert=True
            )
        
        # Increment the mined value
        users_collection.update_one(
            {"_id": user_id},
            {"$inc": {"mined_value": Int64(total_value)}},
            upsert=True
        )
        
        logging.info(f"Users collection updated for user_id: {user_id}")
    except Exception as e:
        logging.error(f"Error updating users collection: {e}")

def get_or_create_and_auth_user(username, password):
    """
    Authenticate a user or create a new one if the user doesn't exist.
    
    Parameters:
    username (str): The username to authenticate.
    password (str): The password to authenticate.
    
    Returns:
    dict: The user document with _id as ObjectId, or None if authentication fails.
    """
    # Check if the user exists
    user = users_collection.find_one({"username": username})
    
    if user:
        # If user exists, verify password
        if check_password_hash(user.get("password_hash", ""), password):
            logging.info(f"User '{username}' authenticated successfully")
            return user  # Return user document with _id as ObjectId
        else:
            logging.warning(f"Failed authentication attempt for user '{username}'")
            return None
    else:
        # Create new user
            password_hash = generate_password_hash(password)
            new_user = {
            "username": username,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        # Insert the new user and get the inserted ID
    user_id = users_collection.insert_one(new_user).inserted_id
        
        # Retrieve the complete user document to ensure _id is an ObjectId
    user = users_collection.find_one({"_id": user_id})
        
    logging.info(f"New user '{username}' created")
    return user  # Return user document with _id as ObjectId

if __name__ == "__main__":
    logging.info("Starting the script...")

    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]

    # Example usage of get_or_create_and_auth_user
    user_name = "Alice"
    user_password = "password"
    user = get_or_create_and_auth_user(user_name, user_password)
    if user:
        logging.info(f"User '{user_name}' authenticated or created successfully with ID: {user['_id']}")
        update_users(user["_id"], sample_elements)
    else:
        logging.error(f"Authentication failed for user '{user_name}'")
    logging.info("Script finished.")