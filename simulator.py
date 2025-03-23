"""
Asteroid Mining Operation Simulator Project Structure

1. find_asteroids.py
   - Retrieves asteroids by name or distance (moid_days).
"""

from config.logging_config import logging  # Import logging configuration
from modules.find_asteroids import find_by_full_name, find_by_distance
from modules.manage_elements import select_elements, sell_elements, find_elements_use
from modules.mine_asteroid import mine_hourly, update_mined_asteroid
from modules.find_value import assess_asteroid_value
from modules.manage_users import get_user, auth_user, update_users
from modules.manage_ships import create_ship, get_ship_by_user_id, update_ship, update_days_in_service, update_cargo, list_cargo, empty_cargo, repair_ship, check_ship_status
from modules.manage_companies import create_company, get_company_value, rank_companies, get_user_id_by_company_name
from modules.manage_mission import get_missions, plan_mission, calculate_mission_risk

def test_find_asteroids():
    logging.info("Testing find_asteroids module...")
    asteroid_full_name = "101955 Bennu (1999 RQ36)"
    asteroid = find_by_full_name(asteroid_full_name)
    logging.info(f"Asteroid: {asteroid}")

def test_manage_elements():
    logging.info("Testing manage_elements module...")
    selected_elements = select_elements(["gold", "platinum", "iron"])
    logging.info(f"Selected elements: {selected_elements}")

    elements_sold = sell_elements(50, selected_elements, {"gold": 50, "platinum": 100, "iron": 10})
    logging.info(f"Elements sold: {elements_sold}")

    elements_by_use = find_elements_use(selected_elements, 100)
    logging.info(f"Elements by use: {elements_by_use}")

def test_manage_ships():
    logging.info("Testing manage_ships module...")
    new_ship = create_ship("Waffle", "Brandon")
    logging.info(f"New ship: {new_ship}")

    ship = get_ship_by_user_id("Brandon")
    logging.info(f"Ship: {ship}")

    updated_ship = update_ship(ship["_id"], {"location": 1, "shield": 90, "days_in_service": 1, "mission": 1, "hull": 95})
    logging.info(f"Updated ship: {updated_ship}")

    update_cargo(ship["_id"], [{"name": "Gold", "mass_kg": 100}])
    cargo = list_cargo(ship["_id"])
    logging.info(f"Cargo: {cargo}")

    empty_cargo(ship["_id"])
    logging.info(f"Cargo emptied for ship ID '{ship['_id']}'.")

    repair_ship(ship["_id"])
    logging.info(f"Ship ID '{ship['_id']}' repaired.")

def test_manage_mission():
    logging.info("Testing manage_mission module...")
    mission_plan = plan_mission("example_uid", "101955 Bennu (1999 RQ36)", 10, 300_000_000)
    logging.info(f"Mission plan: {mission_plan}")

if __name__ == "__main__":
    logging.info("Starting the script...")

    test_find_asteroids()
    test_manage_elements()
    test_manage_ships()
    test_manage_mission()
