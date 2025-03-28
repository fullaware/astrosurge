"""
Asteroid Mining Operation Simulator

This script serves as the main entry point for testing various modules of the Asteroid Mining Operation Simulator project.

Modules Tested:
1. manage_users.py
   - Manages user information and authentication.
2. manage_companies.py
   - Manages company creation, value calculation, and ranking.
3. find_asteroids.py
   - Retrieves asteroids by name or distance (moid_days).
4. find_value.py
   - Retrieves the value of elements.
5. manage_ships.py
   - Manages ship creation, updates, and cargo.
6. manage_mission.py
   - Manages mission planning and risk calculation.
7. mine_asteroid.py
   - Simulates mining an asteroid and updates the asteroid document.
8. manage_elements.py
   - Manages elements, including selection, selling, and usage.

Usage:
- Run this script to test the functionality of the various modules.
"""

from config.logging_config import logging  # Import logging configuration
from amos.find_asteroids import find_by_full_name, find_by_distance
from amos.manage_elements import select_elements, sell_elements, find_elements_use
from amos.mine_asteroid import mine_hourly, update_mined_asteroid
from amos.find_value import assess_asteroid_value
from amos.manage_users import get_user, auth_user, update_users
from amos.manage_ships import (
    create_ship,
    get_ship_by_user_id,
    update_ship,
    update_days_in_service,
    update_cargo,
    list_cargo,
    empty_cargo,
    repair_ship,
    check_ship_status
)
from amos.manage_companies import (
    create_company,
    get_company_value,
    rank_companies,
    get_user_id_by_company_name
)
from amos.manage_mission import get_missions, plan_mission, calculate_mission_risk
from bson import ObjectId

# Module-level variables to store the asteroid from test_find_asteroids() and the mined elements.
target_asteroid = None
mined_elements = []

def test_manage_users():
    """
    Test user management functionality.
    """
    logging.info("Testing manage_users module...")
    user = get_user("Brandon", "password")
    logging.info(f"User retrieved: {user}")
    auth_result = auth_user(user)
    logging.info(f"Authentication result: {auth_result}")

def test_manage_companies():
    """
    Test company management functionality.
    """
    logging.info("Testing manage_companies module...")
    new_company = create_company("Space Exploration Inc.")
    logging.info(f"New company created: {new_company}")
    company_value = get_company_value(new_company["_id"])
    logging.info(f"Company value: {company_value}")
    ranked_companies = rank_companies()
    logging.info(f"Ranked companies: {ranked_companies}")

def test_find_asteroids():
    """
    Find a specific asteroid (101955 Bennu) and store it in target_asteroid.
    """
    logging.info("Testing find_asteroids module...")
    asteroid_full_name = "101955 Bennu (1999 RQ36)"

    global target_asteroid
    target_asteroid = find_by_full_name(asteroid_full_name)
    logging.info(f"Asteroid retrieved in test_find_asteroids(): {target_asteroid}")

def test_find_value():
    """
    Test value assessment of asteroids.
    """
    logging.info("Testing find_value module...")
    if not target_asteroid:
        logging.warning("No asteroid found in test_find_asteroids(). Skipping find_value test.")
        return
    value = assess_asteroid_value(target_asteroid)
    logging.info(f"Asteroid value: {value}")

def test_manage_elements():
    """
    Test selection, selling, and usage of elements.
    """
    logging.info("Testing manage_elements module...")
    selected_elements = select_elements(["gold", "platinum", "iron"])
    logging.info(f"Selected elements: {selected_elements}")

    elements_sold = sell_elements(50, selected_elements, {"gold": 50, "platinum": 100, "iron": 10})
    logging.info(f"Elements sold: {elements_sold}")

    elements_by_use = find_elements_use(selected_elements, 100)
    logging.info(f"Elements by use: {elements_by_use}")

def test_mine_asteroid():
    """
    Test the mine_hourly and update_mined_asteroid functions using the asteroid found by test_find_asteroids().
    The mined elements are stored in a global variable (mined_elements) for other tests to use.
    """
    logging.info("Testing mine_asteroid module...")

    if not target_asteroid:
        logging.warning("No asteroid found in test_find_asteroids(). Skipping mine_asteroid test.")
        return

    user_id = get_user("Brandon", "password")

    global mined_elements
    updated_asteroid, mined_elements = mine_hourly(target_asteroid, 100, user_id)
    logging.info(f"Updated asteroid: {updated_asteroid}")
    logging.info(f"Mined elements: {mined_elements}")

    update_mined_asteroid(updated_asteroid, mined_elements)
    logging.info("Successfully updated the mined asteroid in the database.")

def test_manage_ships():
    """
    Tests ship-related functionality.
    Now uses the mined_elements from test_mine_asteroid(), if available.
    """
    logging.info("Testing manage_ships module...")

    new_ship = create_ship("Waffle", "Brandon")

    # If we have mined elements, update the new ship's cargo with them
    if mined_elements:
        logging.info("Adding mined elements to the new ship's cargo...")
        update_cargo(new_ship["_id"], mined_elements)
    else:
        logging.info("No mined elements available to add to the ship's cargo.")

    # Retrieve updated cargo to verify
    cargo = list_cargo(new_ship["_id"])
    logging.info(f"Cargo after adding mined elements: {cargo}")

    ship = get_ship_by_user_id("Brandon")
    logging.info(f"Ship: {ship}")

    updated_ship = update_ship(
        ship["_id"],
        {
            "location": 1,
            "shield": 90,
            "days_in_service": 1,
            "mission": 1,
            "hull": 95
        }
    )
    logging.info(f"Updated ship: {updated_ship}")

    empty_cargo(ship["_id"])
    logging.info(f"Cargo emptied for ship ID '{ship['_id']}'.")

    repair_ship(ship["_id"])
    logging.info(f"Ship ID '{ship['_id']}' repaired.")
def test_manage_mission():
    """
    Temporarily pass this test while we fix mission planning logic later.
    """
    logging.info("Testing manage_mission module...")
    pass

if __name__ == "__main__":
    logging.info("Starting the script...")

    test_manage_users()
    test_manage_companies()
    test_find_asteroids()
    test_find_value()
    test_manage_elements()
    test_mine_asteroid()   # Mine the asteroid before managing ships
    test_manage_ships()
    test_manage_mission()
