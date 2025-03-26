"""
Asteroid Mining Operation Simulator - Interactive CLI

This script provides a command-line interface for interacting with the simulator.
Users can manage their ships, mine asteroids, and track progress in real-time.

Usage:
    python3 main.py
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
)
from modules.manage_elements import sell_elements
from bson import ObjectId


def main_menu():
    """
    Display the main menu and handle user input.
    """
    print("\nWelcome to the Asteroid Mining Operation Simulator!")
    print("1. Log in")
    print("2. Create a new ship")
    print("3. View your ships")  # Updated text
    print("4. Update ship attributes")
    print("5. Manage cargo")
    print("6. Repair your ship")
    print("7. Check ship status")
    print("8. Exit")

    choice = input("Enter your choice: ")
    return choice


def login():
    """
    Handle user login or account creation.
    """
    print("\n--- Log In or Create Account ---")
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    result = get_or_create_and_auth_user(username, password)
    if result["auth"]:
        logging.info(f"User '{username}' logged in successfully.")
        print(f"Authenticated as: {username}")
        return str(result["user_id"])  # Convert ObjectId to string if needed
    else:
        print("Authentication failed. Please try again.")
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
                ship_details = get_ship(selected_ship["_id"])  # Use the ship's ID to get details
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


def manage_cargo(user_id):
    """
    Manage the cargo of a selected ship.

    Parameters:
    user_id (str): The user ID.
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
    print("4. Sell cargo")  # New option added
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

        sell_dict = {}
        while True:
            cargo_choice = input("Enter the number of the cargo to sell (or 'done' to finish): ").strip()
            if cargo_choice.lower() == "done":
                break
            try:
                cargo_idx = int(cargo_choice) - 1
                if 0 <= cargo_idx < len(cargo):
                    cargo_item = cargo[cargo_idx]
                    sell_mass = int(input(f"Enter the mass (kg) to sell for {cargo_item['name']}: "))
                    if sell_mass > 0 and sell_mass <= cargo_item["mass_kg"]:
                        sell_dict[cargo_item["name"]] = sell_dict.get(cargo_item["name"], 0) + sell_mass
                    else:
                        print("Invalid mass. Please enter a value within the available range.")
                else:
                    print("Invalid choice. Please select a valid cargo number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        if sell_dict:
            sell_elements(50, cargo, sell_dict)  # Call the sell_elements function
            print("Cargo sold.")
            empty_cargo(ship_id)  # Empty the cargo after selling
            print("Cargo emptied after selling.")
    else:
        print("Invalid choice.")


def repair_user_ship(user_id):
    """
    Repair a selected ship for the user.

    Parameters:
    user_id (str): The user ID.
    """
    print("\n--- Repair Your Ship ---")
    selected_ship = view_ships(user_id)  # Allow the user to select a ship
    if not selected_ship:
        print("No ship selected.")
        return

    ship_id = ObjectId(selected_ship["_id"])  # Use the selected ship's ID
    repair_costs = repair_ship(ship_id)  # Call the repair_ship function with the selected ship's ID
    print(f"Your ship '{selected_ship['name']}' has been repaired at a cost of $ {repair_costs}.")


def update_ship_menu(user_id):
    """
    Update attributes of a selected ship through the CLI menu.

    Parameters:
    user_id (str): The user ID.
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
        elif choice == "8":
            print("Exiting the simulator. Goodbye!")
            break
        else:
            print("Invalid choice or you need to log in first.")


if __name__ == "__main__":
    main()