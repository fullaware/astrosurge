from logging_config import logging  # Import logging configuration
from mongodb_config import users_collection  # Import MongoDB configuration

def create_company(uid: str, company_name: str) -> bool:
    """
    Create a company for the user with the given UID and company name.

    Parameters:
    uid (str): The user ID.
    company_name (str): The desired company name.

    Returns:
    bool: True if the company is created successfully, False if the company name is already in use.
    """
    existing_company = users_collection.find_one({'company_name': company_name})
    if existing_company:
        logging.error(f"Company name '{company_name}' is already in use.")
        return False

    users_collection.update_one(
        {'uid': uid},
        {'$set': {'company_name': company_name}},
        upsert=True
    )
    logging.info(f"Company '{company_name}' created for user {uid}.")
    return True

def get_company_value(uid: str) -> int:
    """
    Calculate the total value of a user's company.

    Parameters:
    uid (str): The user ID.

    Returns:
    int: The total value of the company.
    """
    user = users_collection.find_one({'uid': uid})
    if not user:
        logging.error(f"User with uid '{uid}' not found.")
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

def get_uid_by_company_name(company_name: str) -> str:
    """
    Get the UID of a user by their company name.

    Parameters:
    company_name (str): The company name.

    Returns:
    str: The UID of the user, or None if not found.
    """
    user = users_collection.find_one({'company_name': company_name})
    if user:
        return user['uid']
    logging.error(f"Company name '{company_name}' not found.")
    return None

if __name__ == "__main__":
    logging.info("Starting the script...")

    # Example usage of create_company
    user_uid = "Brandon"
    company_created = create_company(user_uid, "Example Company")
    logging.info(f"Company created: {company_created}")

    # Example usage of get_company_value
    company_value = get_company_value(user_uid)
    logging.info(f"Company value for UID {user_uid}: {company_value}")

    # Example usage of rank_companies
    companies_ranked = rank_companies()
    logging.info(f"Ranked companies: {companies_ranked}")

    # Example usage of get_uid_by_company_name
    uid_by_company = get_uid_by_company_name("Example Company")
    logging.info(f"UID for company 'Example Company': {uid_by_company}")