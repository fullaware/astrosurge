"""
main.py

This module serves as the entry point for managing asteroid mining missions. The primary objectives are:

1. **Find an Asteroid**:
   - Locate an asteroid using its name or distance from Earth.
   - Assess its value and plan a mission to mine its resources.

2. **Plan a Mission**:
   - Create a mission to mine the asteroid, assigning a ship and calculating costs.
   - Define the planned duration and investment required for the mission.

3. **Execute the Mission**:
   - Simulate the mission day by day using `execute_mining_mission`.
   - Follow the mission plan:
     a. Travel to the asteroid by incrementing or decrementing `ship.location` until it matches the asteroid's distance.
     b. Mine the asteroid by removing `mass_kg` from its elements and depositing them into the ship's cargo.
     c. Travel back to Earth by updating `ship.location` until it reaches `0` (Earth).
     d. Deposit the mined resources into the mission's `mined_elements` list.

4. **Sell Resources**:
   - Once the ship returns to Earth, sell the mined elements and update the user's/company's `bank` field with the proceeds.

5. **Track Mission Progress**:
   - Maintain the state of the mission by updating the `mission` document and `ship` variables daily.
   - Track the `actual_duration` of the mission and calculate additional costs incurred each day.

6. **Mission Completion**:
   - A mission is marked as "Mission Success" if the ship completes the trip and deposits its cargo on Earth.
   - A mission is marked as "Mission Failure" if the ship's `hull` reaches `0` before returning to Earth.

This module ensures that the mining process is realistic and adheres to the planned objectives, allowing for iterative execution of missions while maintaining accurate state tracking.
"""

from config.logging_config import logging  # Use the centralized logging configuration
from modules.manage_users import get_or_create_and_auth_user
from modules.manage_ships import (
    create_ship,
    get_ships_by_user_id,
    get_ship,
    update_ship_cargo,
    update_ship_attributes,
    list_cargo,
    empty_cargo,
    repair_ship,
    get_current_cargo_mass
)
from modules.manage_elements import sell_elements, find_elements_use
from modules.manage_mission import get_missions, plan_mission, fund_mission, MissionStatus, update_mission
from modules.execute_mission import execute_mission, deposit_cargo
from modules.find_asteroids import find_by_full_name, find_by_distance
from modules.find_value import initialize_commodity_values, commodity_values
from modules.manage_companies import (
    create_company,
    get_company_value,
    rank_companies,
    get_user_id_by_company_name
)
from modules.mine_asteroid import mine_hourly, update_mined_asteroid, get_mined_asteroid_by_name
from bson import ObjectId


def main_menu():
    """
    Display the main menu and handle user input.
    """
    print("\nWelcome to the Asteroid Mining Operation Simulator!")
    print("1. Log in")
    print("2. Create a new ship")
    print("3. View your ships")
    print("4. Update ship attributes")
    print("5. Manage cargo")
    print("6. Repair your ship")
    print("7. Check ship status")
    print("8. Manage missions")  # New option added
    print("9. Exit")

    choice = input("Enter your choice: ")
    return choice


def login():
    """User login function"""
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    user = get_or_create_and_auth_user(username, password)
    if user:
        print(f"Welcome, {username}!")
        return ObjectId(user["_id"])  # Convert to ObjectId immediately
    else:
        print("Invalid credentials.")
        return None


def create_new_ship(user_id):
    """
    Create a new ship for the logged-in user.
    """
    print("\n--- Create a New Ship ---")
    while True:
        ship_name = input("Enter a name for your ship: ").strip()
        if ship_name:
            break
        print("Ship name cannot be empty. Please enter a valid name.")

    ship = create_ship(ship_name, user_id)
    print(f"Ship created: {ship}")
    return ship


def view_ship(user_id):
    """
    View a specific ship associated with the user.
    """
    print("\n--- View Your Ship ---")
    ships = get_ships_by_user_id(user_id)

    if not ships:
        print("No ships found for your user ID.")
        return

    print(f"You have {len(ships)} ship(s):")
    for idx, ship in enumerate(ships):
        print(f"{idx + 1}. Name: {ship['name']}, ID: {ship['_id']}")

    while True:
        try:
            choice = int(input("Enter the number of the ship you want to view: ")) - 1
            if 0 <= choice < len(ships):
                selected_ship = ships[choice]
                ship_details = get_ship(ObjectId(selected_ship["_id"]))  # Convert to ObjectId
                print(f"Selected ship details: {ship_details}")
                return
            else:
                print("Invalid choice. Please select a valid ship number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def view_ships(user_id):
    """
    View all ships associated with the user and allow selection of a specific ship.

    Parameters:
    user_id (str): The user ID.

    Returns:
    dict: The selected ship document, or None if no valid selection is made.
    """
    print("\n--- View Your Ships ---")
    ships = get_ships_by_user_id(user_id)

    if not ships:
        print("No ships found for your user ID.")
        return None

    print(f"You have {len(ships)} ship(s):")
    for idx, ship in enumerate(ships):
        print(f"{idx + 1}. Name: {ship['name']}, ID: {ship['_id']}, Cargo: {ship.get('cargo', [])}")

    while True:
        try:
            choice = int(input("Enter the number of the ship you want to select: ")) - 1
            if 0 <= choice < len(ships):
                selected_ship = ships[choice]
                print(f"Selected ship: {selected_ship['name']} (ID: {selected_ship['_id']})")
                return selected_ship
            else:
                print("Invalid choice. Please select a valid ship number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def manage_cargo(user_id: ObjectId):
    """
    Manage the cargo of a selected ship.

    Parameters:
    user_id (ObjectId): The user ID.
    """
    print("\n--- Manage Cargo ---")
    selected_ship = view_ships(user_id)  # Allow the user to select a ship
    if not selected_ship:
        return

    ship_id = ObjectId(selected_ship["_id"])  # Use the selected ship's ID
    print(f"Managing cargo for ship: {selected_ship['name']} (ID: {ship_id})")

    print("1. View cargo")
    print("2. Add cargo")
    print("3. Empty cargo")
    print("4. Sell cargo")  # Updated sell cargo option
    choice = input("Enter your choice: ")

    if choice == "1":
        cargo = list_cargo(ship_id)
        print(f"Cargo: {cargo}")
    elif choice == "2":
        new_cargo = []
        while True:
            cargo_name = input("Enter the name of the cargo (or 'done' to finish): ").strip()
            if cargo_name.lower() == "done":
                break
            try:
                cargo_mass = int(input(f"Enter the mass (kg) for {cargo_name}: "))
                new_cargo.append({"name": cargo_name, "mass_kg": cargo_mass})
            except ValueError:
                print("Invalid mass. Please enter a valid integer.")

        if new_cargo:
            update_ship_cargo(ship_id, new_cargo)
            print("Cargo added.")
    elif choice == "3":
        empty_cargo(ship_id)
        print("Cargo emptied.")
    elif choice == "4":  # Sell cargo option
        cargo = list_cargo(ship_id)
        if not cargo:
            print("No cargo to sell.")
            return

        print("Available cargo:")
        for idx, item in enumerate(cargo):
            print(f"{idx + 1}. {item['name']} - {item['mass_kg']} kg")

        while True:
            try:
                percentage = float(input("Enter the percentage of cargo to sell (0-100): "))
                if 0 <= percentage <= 100:
                    break
                else:
                    print("Invalid percentage. Please enter a value between 0 and 100.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Calculate the amount to sell for each cargo item
        sell_dict = []
        remaining_cargo = []
        for item in cargo:
            sell_mass = int(item["mass_kg"] * (percentage / 100))
            remaining_mass = item["mass_kg"] - sell_mass
            if sell_mass > 0:
                sell_dict.append({"name": item["name"], "mass_kg": sell_mass})
            if remaining_mass > 0:
                remaining_cargo.append({"name": item["name"], "mass_kg": remaining_mass})

        if sell_dict:
            sell_elements(ship_id, sell_dict, commodity_values)  # Call the sell_elements function
            update_ship_cargo(ship_id, remaining_cargo)  # Update the cargo with remaining items
            print(f"Sold {percentage}% of all cargo.")
        else:
            print("No cargo was sold.")
    else:
        print("Invalid choice.")


def repair_user_ship(user_id: ObjectId):
    """
    Repair a selected ship for the user.

    Parameters:
    user_id (ObjectId): The user ID.
    """
    print("\n--- Repair Your Ship ---")
    selected_ship = view_ships(user_id)  # Allow the user to select a ship
    if not selected_ship:
        print("No ship selected.")
        return

    ship_id = ObjectId(selected_ship["_id"])  # Convert to ObjectId
    repair_costs = repair_ship(ship_id)  # Call the repair_ship function with the selected ship's ID
    print(f"Your ship '{selected_ship['name']}' has been repaired at a cost of $ {repair_costs}.")


def update_ship_menu(user_id: ObjectId):
    """
    Update attributes of a selected ship through the CLI menu.

    Parameters:
    user_id (ObjectId): The user ID.
    """
    print("\n--- Update Ship Attributes ---")
    selected_ship = view_ships(user_id)  # Allow the user to select a ship
    if not selected_ship:
        return

    ship_id = ObjectId(selected_ship["_id"])  # Use the selected ship's ID
    print(f"Updating attributes for ship: {selected_ship['name']} (ID: {ship_id})")

    updates = {}
    location = input("Enter new location (leave blank to skip): ")
    if location:
        updates["location"] = int(location)

    shield = input("Enter new shield value (leave blank to skip): ")
    if shield:
        updates["shield"] = int(shield)

    hull = input("Enter new hull value (leave blank to skip): ")
    if hull:
        updates["hull"] = int(hull)

    updated_ship = update_ship_attributes(ship_id, updates)  # Call the core function in manage_ships.py
    print(f"Updated ship: {updated_ship}")


def manage_missions(user_id: ObjectId):
    """
    Manage missions for the user.

    Parameters:
        user_id (ObjectId): The user ID.
    """
    print("\n--- Manage Missions ---")
    print("1. View missions")
    print("2. Plan a new mission")
    print("3. Fund a mission")
    print("4. Execute a mission (complete)")
    print("5. Execute a single day of a mission")
    print("6. Exit")

    choice = input("Enter your choice: ").strip()
    logging.info(f"User {user_id} is managing missions. Selected option: {choice}")

    if choice == "1":
        # View missions
        missions = get_missions(user_id)
        if missions:
            for mission in missions:
                print(f"Mission ID: {mission.id}, Asteroid: {mission.asteroid_name}, Status: {mission.status.name}")
        else:
            print("No missions found.")
    elif choice == "2":
        # Plan a new mission
        asteroid_name = input("Enter the asteroid name: ").strip()
        ship_cost = int(input("Enter the ship cost (default: 150000000): ").strip() or 150_000_000)
        operational_cost_per_day = int(input("Enter the operational cost per day (default: 50000): ").strip() or 50_000)

        selected_ship = view_ships(user_id)
        if not selected_ship:
            print("No ship selected. Cannot plan mission.")
            return

        ship_id = ObjectId(selected_ship["_id"])
        mission = plan_mission(
            user_id=user_id,
            ship_id=ship_id,
            asteroid_name=asteroid_name,
            ship_cost=ship_cost,
            operational_cost_per_day=operational_cost_per_day
        )
        if mission:
            print(f"Mission planned successfully: {mission}")
        else:
            print("Failed to plan mission.")
    elif choice == "3":
        # Fund a mission
        missions = get_missions(user_id)
        if not missions:
            print("No missions available to fund.")
            return

        print("Available missions:")
        for idx, mission in enumerate(missions):
            print(f"{idx + 1}. Mission ID: {mission.id}, Asteroid: {mission.asteroid_name}, Status: {mission.status.name}")

        while True:
            try:
                mission_choice = int(input("Enter the number of the mission to fund: ")) - 1
                if 0 <= mission_choice < len(missions):
                    selected_mission = missions[mission_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid mission number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        amount = int(input("Enter the amount to fund: ").strip())
        fund_mission(selected_mission.id, user_id, amount)
        print(f"Mission '{selected_mission.asteroid_name}' funded successfully.")
    elif choice == "4":
        # Execute a mission (complete)
        missions = get_missions(user_id)
        if not missions:
            print("No missions available.")
            return

        eligible_missions = [m for m in missions if m.status in [MissionStatus.FUNDED, MissionStatus.EXECUTING]]
        if not eligible_missions:
            print("No missions available to execute. Missions must be FUNDED or EXECUTING.")
            return

        print("Available missions to execute:")
        for idx, mission in enumerate(eligible_missions):
            print(f"{idx + 1}. Mission ID: {mission.id}, Asteroid: {mission.asteroid_name}, Status: {mission.status.name}")

        while True:
            try:
                mission_choice = int(input("Enter the number of the mission to execute: ")) - 1
                if 0 <= mission_choice < len(eligible_missions):
                    selected_mission = eligible_missions[mission_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid mission number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Execute the mission day by day until completed or failed
        while True:
            execute_mining_mission(user_id, selected_mission.id)
            mission = get_missions(user_id, mission_id=selected_mission.id)
            if mission.status in [MissionStatus.COMPLETED, MissionStatus.FAILED]:
                break
    elif choice == "5":
        # Execute a single day of a mission
        missions = get_missions(user_id)
        if not missions:
            print("No missions available.")
            return

        eligible_missions = [m for m in missions if m.status in [MissionStatus.FUNDED, MissionStatus.EXECUTING]]
        if not eligible_missions:
            print("No missions available to execute. Missions must be FUNDED or EXECUTING.")
            return

        print("Available missions to execute a single day:")
        for idx, mission in enumerate(eligible_missions):
            print(f"{idx + 1}. Mission ID: {mission.id}, Asteroid: {mission.asteroid_name}, Status: {mission.status.name}")

        while True:
            try:
                mission_choice = int(input("Enter the number of the mission to execute a single day: ")) - 1
                if 0 <= mission_choice < len(eligible_missions):
                    selected_mission = eligible_missions[mission_choice]
                    break
                else:
                    print("Invalid choice. Please select a valid mission number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Execute a single day of the mission
        execute_mining_mission(user_id, selected_mission.id)
    elif choice == "6":
        # Exit mission management
        print("Exiting mission management.")
    else:
        print("Invalid choice.")


def manage_mining(user_id: ObjectId, ship_id: ObjectId, asteroid_name: str):
    ship = get_ship(ship_id)
    ship_capacity = ship.get('capacity', 50000)
    current_cargo_mass = get_current_cargo_mass(ship_id)

    # Perform mining
    mined_elements, at_capacity = mine_hourly(
        asteroid_name=asteroid_name,
        extraction_rate=ship.get("mining_power", 100),
        user_id=user_id,
        ship_capacity=ship_capacity,
        current_cargo_mass=current_cargo_mass
    )

    logging.info(f"Mined elements: {mined_elements}")
    logging.info(f"Current cargo mass: {current_cargo_mass}, Ship capacity: {ship_capacity}")

    if mined_elements:
        update_ship_cargo(ship_id, mined_elements)
        logging.info(f"Updated cargo for ship ID {ship_id}.")
    else:
        logging.warning("No elements were mined.")


def execute_mining_mission(user_id: ObjectId, mission_id: ObjectId):
    """
    Execute a single day of the mining mission.
    """
    # Retrieve mission and ship details
    missions = get_missions(user_id)
    mission = next((m for m in missions if m.id == mission_id), None)
    if not mission:
        print("Mission not found.")
        return

    ship = get_ship(mission.ship_id)
    asteroid_distance = mission.distance
    asteroid_name = mission.asteroid_name

    # Check if the mission is already completed or failed
    if mission.status == MissionStatus.SUCCESS:
        print("Mission already completed.")
        return
    if mission.status == MissionStatus.FAILED:
        print("Mission has already failed.")
        return

    # Increment the actual duration
    mission.actual_duration += 1
    update_mission(mission_id, {"actual_duration": mission.actual_duration})

    # Calculate additional costs
    additional_cost = mission.actual_duration * ship.get("operational_cost_per_day", 50000)
    update_mission(mission_id, {"total_cost": mission.investment + additional_cost})

    # Travel to the asteroid
    if ship["location"] != asteroid_distance:
        if ship["hull"] <= 0:
            mission.status = MissionStatus.FAILED
            update_mission(mission_id, {"status": MissionStatus.FAILED})
            print("Mission failed: Ship hull is at 0 before reaching the asteroid.")
            return

        # Increment or decrement ship location
        if ship["location"] < asteroid_distance:
            ship["location"] += 1
        elif ship["location"] > asteroid_distance:
            ship["location"] -= 1

        update_ship_attributes(ship["_id"], {"location": ship["location"]})
        print(f"Traveling to asteroid... Current location: {ship['location']}")
        return  # End the day after traveling

    # Mine the asteroid
    if ship.location == asteroid_distance:
        ship_capacity = ship.get("capacity", 50000)
        current_cargo_mass = get_current_cargo_mass(ship["_id"])

        if current_cargo_mass < ship_capacity:
            mined_elements, at_capacity = mine_hourly(
                asteroid_name=asteroid_name,
                extraction_rate=ship.get("mining_power", 100),
                user_id=user_id,
                ship_capacity=ship_capacity,
                current_cargo_mass=current_cargo_mass,
            )

            if mined_elements:
                update_ship_cargo(ship["_id"], mined_elements)
                print(f"Mined elements: {mined_elements}")
            else:
                print("No more elements to mine from the asteroid.")
        else:
            print("Ship cargo is full. Preparing to return to Earth.")
            return  # End the day after mining

    # Travel back to Earth
    if ship.location != 0:
        if ship.hull <= 0:
            mission.status = MissionStatus.FAILED
            update_mission(mission_id, {"status": MissionStatus.FAILED})
            print("Mission failed: Ship hull is at 0 before reaching Earth.")
            return

        # Increment or decrement ship location
        if ship.location > 0:
            ship.location -= 1

        update_ship_attributes(ship["_id"], {"location": ship.location})
        print(f"Returning to Earth... Current location: {ship.location}")
        return  # End the day after traveling

    # Deposit cargo into the mission
    if ship.location == 0:
        cargo = list_cargo(ship["_id"])
        if cargo:
            deposit_cargo(mission_id, cargo)
            empty_cargo(ship["_id"])
            print("Cargo deposited into the mission.")

        # Mark the mission as successful
        update_mission(mission_id, {"status": MissionStatus.SUCCESS})
        print("Mission completed successfully!")


def main():
    """
    Main function to run the CLI.
    """
    user_id = None

    while True:
        choice = main_menu()

        if choice == "1":
            user_id = login()
        elif choice == "2" and user_id:
            create_new_ship(user_id)
        elif choice == "3" and user_id:
            view_ships(user_id)
        elif choice == "4" and user_id:
            update_ship_menu(user_id)
        elif choice == "5" and user_id:
            manage_cargo(user_id)
        elif choice == "6" and user_id:
            repair_user_ship(user_id)
        elif choice == "7" and user_id:
            selected_ship = view_ships(user_id)  # Allow the user to select a ship
            if selected_ship:
                ship_id = ObjectId(selected_ship["_id"])  # Convert to ObjectId
                get_ship(ship_id)
            else:
                print("No ship selected.")
        elif choice == "8" and user_id:
            manage_missions(user_id)  # New option to manage missions
        elif choice == "9":
            print("Exiting the simulator. Goodbye!")
            break
        else:
            print("Invalid choice or you need to log in first.")


if __name__ == "__main__":
    initialize_commodity_values()  # Initialize the commodity values
    main()