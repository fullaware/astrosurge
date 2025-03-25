"""
Asteroid Mining Command-Line Interface

This script recreates the user experience at the command line:
1. Authenticate user
2. Create or join a company
3. Find asteroids and select from a short list
4. Plan and fund a mission
5. Execute mission: travel, mine, return
6. Sell elements
7. Update user’s accumulated wealth

Usage:
    python3 main.py
"""

import sys
from colorama import init, Fore, Style
init(autoreset=True)

from modules.manage_users import get_user, auth_user
from modules.manage_companies import create_company, get_company_value
from modules.find_asteroids import find_by_distance, find_by_full_name
from modules.find_value import assess_asteroid_value
from modules.manage_ships import create_ship, update_cargo, list_cargo
from modules.manage_mission import plan_mission, calculate_mission_risk, fund_mission, execute_mission
from modules.mine_asteroid import mine_hourly, update_mined_asteroid
from modules.manage_elements import sell_elements

def main():
    print(Fore.GREEN + "Welcome to the Asteroid Mining CLI!")
    print(Style.RESET_ALL)

    # 1. Authenticate user (with a retry mechanism)
    user_id = None
    while not user_id:
        username = input(Fore.CYAN + "Enter your username: " + Style.RESET_ALL).strip()
        password = input(Fore.CYAN + "Enter your password: " + Style.RESET_ALL).strip()

        user_record = get_user(username)
        if user_record and auth_user(user_record["_id"], password):
            user_id = user_record["_id"]
        else:
            print(Fore.RED + f"User '{username}' not found or invalid password." + Style.RESET_ALL)
            choice = input(Fore.YELLOW + "Would you like to try again? (y/n): " + Style.RESET_ALL).lower().strip()
            if choice != 'y':
                print(Fore.RED + "Exiting..." + Style.RESET_ALL)
                sys.exit(1)

    # 2. Create or join a company
    company_name = input(Fore.CYAN + "Enter your company name (or a new one to create): " + Style.RESET_ALL).strip()
    result = create_company(company_name, user_id)
    if result:
        print(Fore.GREEN + f"Successfully joined or created company: {company_name}" + Style.RESET_ALL)
    else:
        print(Fore.RED + "Failed to create or join company. Check logs." + Style.RESET_ALL)
        sys.exit(1)

    # 3. Find asteroids and select from a short list
    print(Fore.CYAN + "Finding three candidate asteroids...\n" + Style.RESET_ALL)
    candidate_asteroids = [
        find_by_full_name("101955 Bennu (1999 RQ36)"),
        find_by_full_name("99942 Apophis (2004 MN4)"),
        find_by_full_name("162173 Ryugu (1999 JU3)")
    ]
    for i, asteroid in enumerate(candidate_asteroids, start=1):
        if asteroid:
            print(f"{i}. {asteroid.get('full_name', 'Unknown')} (ID: {asteroid.get('_id')})")
        else:
            print(f"{i}. (Not found)")

    choice = int(input(Fore.CYAN + "\nChoose an asteroid by number: " + Style.RESET_ALL).strip()) - 1
    if choice < 0 or choice >= len(candidate_asteroids) or not candidate_asteroids[choice]:
        print(Fore.RED + "Invalid choice or asteroid not found. Exiting." + Style.RESET_ALL)
        sys.exit(1)

    target_asteroid = candidate_asteroids[choice]
    print(Fore.GREEN + f"Selected asteroid: {target_asteroid.get('full_name')}\n" + Style.RESET_ALL)

    # 4. Plan and fund a mission
    print(Fore.CYAN + "Planning a mission..." + Style.RESET_ALL)
    mission_plan = plan_mission(user_id, target_asteroid["full_name"], 10, 300_000_000)
    if not mission_plan:
        print(Fore.RED + "Failed to plan mission. Exiting." + Style.RESET_ALL)
        sys.exit(1)

    risk = calculate_mission_risk(target_asteroid, mission_plan)
    print(f"Mission Risk: {risk:.2f}")

    if not fund_mission(mission_plan["_id"], user_id, 50000):
        print(Fore.RED + "Failed to fund mission. Exiting." + Style.RESET_ALL)
        sys.exit(1)
    print(Fore.GREEN + "Mission funded successfully!\n" + Style.RESET_ALL)

    # 5. Execute mission: travel, mine, return
    if not execute_mission(mission_plan["_id"]):
        print(Fore.RED + "Mission execution failed. Exiting." + Style.RESET_ALL)
        sys.exit(1)
    print(Fore.GREEN + "Traveled to asteroid successfully!\n" + Style.RESET_ALL)

    updated_asteroid, mined_elements = mine_hourly(target_asteroid, 100, user_id)
    update_mined_asteroid(updated_asteroid, mined_elements)
    print(Fore.YELLOW + "Mining completed successfully!" + Style.RESET_ALL)
    print(f"Mined Elements: {mined_elements}\n")

    # Return to Earth
    print(Fore.CYAN + "Returning to Earth..." + Style.RESET_ALL)
    print(Fore.GREEN + "Safely returned to Earth!\n" + Style.RESET_ALL)

    # 6. Sell elements
    sell_dict = {}
    for elem in mined_elements:
        half_mass = elem["mass_kg"] // 2
        if half_mass > 0:
            sell_dict[elem["name"]] = sell_dict.get(elem["name"], 0) + half_mass
    sale_result = sell_elements(50, mined_elements, sell_dict)
    print(Fore.GREEN + f"Sold elements: {sale_result}" + Style.RESET_ALL)

    # 7. Update user’s wealth (placeholder logic)
    print(Fore.GREEN + "Workflow complete! Congratulations on your successful asteroid mining mission.\n" + Style.RESET_ALL)

if __name__ == "__main__":
    main()