from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import users_collection  # Import MongoDB configuration
from bson import ObjectId

def create_company(user_id: ObjectId, company_name: str) -> bool:
    """
    Create a company for the user with the given user ID and company name.

    Parameters:
    user_id (ObjectId): The user ID.
    company_name (str): The desired company name.

    Returns:
    bool: True if the company is created successfully, False if the company name is already in use.
    """
    existing_company = users_collection.find_one({'company_name': company_name})
    if existing_company:
        logging.error(f"Company name '{company_name}' is already in use.")
        return False

    users_collection.update_one(
        {'_id': user_id},
        {'$set': {'company_name': company_name}},
        upsert=True
    )
    logging.info(f"Company '{company_name}' created for user {user_id}.")
    return True

def get_company_value(user_id: ObjectId) -> int:
    """
    Calculate the total value of a user's company.

    Parameters:
    user_id (ObjectId): The user ID.

    Returns:
    int: The total value of the company.
    """
    user = users_collection.find_one({'_id': user_id})
    if not user:
        logging.error(f"User with ID '{user_id}' not found.")
        return 0

    total_value = user.get('mined_value', 0)
    return total_value

def rank_companies() -> list:
    """
    Rank companies based on their total value and elements mined.

    Returns:
    list: A list of companies ranked by their total value and elements mined.
    """
    companies = users_collection.find()
    ranked_companies = sorted(companies, key=lambda x: x.get('mined_value', 0), reverse=True)
    return ranked_companies

def get_user_id_by_company_name(company_name: str) -> ObjectId:
    """
    Get the user ID of a user by their company name.

    Parameters:
    company_name (str): The company name.

    Returns:
    ObjectId: The user ID, or None if not found.
    """
    user = users_collection.find_one({'company_name': company_name})
    if user:
        return user['_id']
    logging.error(f"Company name '{company_name}' not found.")
    return None

def evaluate_mission_plan(mission_plan: dict) -> float:
    """
    Evaluate the mission plan and return the expected ROI multiplier.
    """
    base_roi = 1.25
    risk_factor = mission_plan.get("risk", 1.0)
    return base_roi * risk_factor

def fund_mission(user_id: ObjectId, mission_plan: dict) -> bool:
    """
    Deduct funds from the user's account and fund the mission.
    """
    user = users_collection.find_one({"_id": user_id})
    if not user:
        raise ValueError("User not found.")

    required_funds = mission_plan["cost"]
    if user["bank"] < required_funds:
        raise ValueError("Insufficient funds.")

    users_collection.update_one({"_id": user_id}, {"$inc": {"bank": -required_funds}})
    return True

if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example usage of create_company
    user_id = ObjectId("60d5f9b8f8d2f8a0b8f8d2f8")  # Example ObjectId
    company_created = create_company(user_id, "Example Company")
    logging.info(f"Company created: {company_created}")

    # Example usage of get_company_value
    company_value = get_company_value(user_id)
    logging.info(f"Company value for user ID {user_id}: {company_value}")

    # Example usage of rank_companies
    companies_ranked = rank_companies()
    logging.info(f"Ranked companies: {companies_ranked}")

    # Example usage of get_user_id_by_company_name
    user_id_by_company = get_user_id_by_company_name("Example Company")
    logging.info(f"User ID for company 'Example Company': {user_id_by_company}")