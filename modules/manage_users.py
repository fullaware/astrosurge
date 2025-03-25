from werkzeug.security import generate_password_hash, check_password_hash
from modules.find_value import assess_element_values, commodity_values  # Update the import path for find_value
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import users_collection  # Import MongoDB configuration
from bson import Int64, ObjectId  # Import Int64 and ObjectId from bson

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

def get_or_create_and_auth_user(name: str, password: str) -> dict:
    """
    Get or create a user with the given name and password. If the user exists, authenticate them.
    If the user does not exist, create a new user with the specified name and password, and authenticate them.

    Parameters:
    name (str): The name of the user.
    password (str): The password of the user.

    Returns:
    dict: A dictionary containing the user ID and authentication status.
           Example: {"user_id": ObjectId, "auth": True/False}
    """
    try:
        # Check if the user exists
        user = users_collection.find_one({'name': name})
        if user:
            # User exists, attempt authentication
            if check_password_hash(user['password'], password):
                logging.info(f"User '{name}' authenticated successfully.")
                return {"user_id": user['_id'], "auth": True}
            else:
                logging.warning(f"Authentication failed for user '{name}'. Incorrect password.")
                return {"user_id": user['_id'], "auth": False}
        else:
            # User does not exist, create a new user
            new_user = {
                'name': name,
                'bank': Int64(0),
                'password': generate_password_hash(password)  # Hash the provided password
            }
            users_collection.insert_one(new_user)
            logging.info(f"New user created: {new_user}")
            return {"user_id": new_user['_id'], "auth": True}
    except Exception as e:
        logging.error(f"Error in get_or_create_and_auth_user: {e}")
        return {"user_id": None, "auth": False}

if __name__ == "__main__":
    logging.info("Starting the script...")

    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]

    # Example usage of get_user
    user_name = "Alice"
    user_password = "password"
    user_id = get_user(user_name, user_password)
    logging.info(f"User ID for {user_name}: {user_id}")

    # Example usage of auth_user
    is_authenticated = auth_user(user_id, user_password)
    logging.info(f"Authentication successful: {is_authenticated}")

    update_users(user_id, sample_elements)
    logging.info("Script finished.")