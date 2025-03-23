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

def get_user(name: str, password: str) -> ObjectId:
    """
    Get or create a user with the given name and password. If the user exists, return the existing user ID.
    Otherwise, create a new user with the specified name and password, and a bank balance of 0, and return the new user ID.

    Parameters:
    name (str): The name of the user.
    password (str): The password of the user.

    Returns:
    ObjectId: The user ID.
    """
    user = users_collection.find_one({'name': name})
    if user:
        logging.info(f"User with name '{name}' already exists: {user}")
        return user['_id']

    new_user = {
        'name': name,
        'bank': Int64(0),
        'password': generate_password_hash(password)  # Set the provided password
    }
    users_collection.insert_one(new_user)
    logging.info(f"New user added: {new_user}")
    return new_user['_id']

def auth_user(user_id: ObjectId, password: str) -> bool:
    """
    Authenticate a user with the given user ID and password.

    Parameters:
    user_id (ObjectId): The user ID.
    password (str): The password to authenticate.

    Returns:
    bool: True if authentication is successful, False otherwise.
    """
    user = users_collection.find_one({'_id': user_id})
    if user and check_password_hash(user['password'], password):
        logging.info(f"User {user_id} authenticated successfully.")
        return True
    logging.error(f"Authentication failed for user {user_id}.")
    return False

def get_user_id_by_user_name(user_name: str) -> ObjectId:
    """
    Get the user ID of a user by their user name.

    Parameters:
    user_name (str): The user name.

    Returns:
    ObjectId: The user ID, or None if not found.
    """
    user = users_collection.find_one({'name': user_name})
    if user:
        return user['_id']
    logging.error(f"User name '{user_name}' not found.")
    return None

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

    # Example usage of get_user_id_by_user_name
    user_id_by_user = get_user_id_by_user_name("Alice")
    logging.info(f"User ID for user 'Alice': {user_id_by_user}")