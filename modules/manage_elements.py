import math
from pprint import pprint
from config.logging_config import logging  # Import logging configuration
from config.mongodb_config import users_collection, elements_collection  # Import MongoDB configuration
from bson import Int64  # Import Int64 from bson

VALID_ELEMENTS = ["gold", "silver", "platinum", "copper", "palladium"]

def select_elements(element_names: list) -> list:
    """
    Select elements based on their names and return a list of dictionaries with element details.

    Parameters:
    element_names (list): A list of element names.

    Returns:
    list: A list of dictionaries with element details.
    """
    elements = []
    for name in element_names:
        elements.append({"name": name, "mass_kg": 100})  # Example mass, replace with actual logic
    return elements

def find_elements_use(elements: list, total_mined_mass: int) -> list:
    """
    This function processes the elements and categorizes them by their use.

    For each element, find it in the `asteroids.elements` collection. 
    Extract its `use` field and categorize the elements by their use.
    return a list of elements categorized by use and their total mass.
    """
    elements_by_use = []
    usecases_dict = {}

    for element in elements:
        element_name = element.get('name')
        mass_kg = element.get('mass_kg')

        db_element = elements_collection.find_one({'name': element_name})
        if db_element:
            uses = db_element.get('uses', [])
            for use in uses:
                if use not in usecases_dict:
                    usecases_dict[use] = Int64(0)
                usecases_dict[use] += Int64(mass_kg)

    # Ensure the total mass allocated to each use is less than the total mined mass
    total_allocated_mass = sum(usecases_dict.values())
    if total_allocated_mass > total_mined_mass:
        scale_factor = total_mined_mass / total_allocated_mass
        for use in usecases_dict:
            usecases_dict[use] = Int64(usecases_dict[use] * scale_factor)

    for use, total_mass in usecases_dict.items():
        elements_by_use.append({
            "use": use,
            "total_mass_kg": math.ceil(total_mass)
        })

    return elements_by_use

def sell_elements(percentage: int, cargo_list: list, commodity_values: dict) -> dict:
    """
    Sell a percentage of each element in the cargo list.

    Parameters:
    percentage (int): The percentage of each element to sell.
    cargo_list (list): The list of elements in the cargo.
    commodity_values (dict): The dictionary of commodity values.

    Returns:
    dict: A dictionary of elements with their total value.
    """
    try:
        total_value = Int64(0)
        elements_sold = {}
        for element in cargo_list:
            element_name = element['name']
            mass_kg = element['mass_kg']
            value_per_kg = commodity_values.get(element_name.lower(), 0)
            sell_mass = mass_kg * (percentage / 100)
            sell_value = sell_mass * value_per_kg
            total_value += Int64(sell_value)
            elements_sold[element_name] = Int64(sell_value)
            logging.info(f"Sold {sell_mass} kg of {element_name} for {sell_value} $")

        logging.info(f"Total value of sold elements: {total_value} $")
        return elements_sold
    except Exception as e:
        logging.error(f"Error selling elements: {e}")
        return {}

if __name__ == "__main__":
    sample_elements = [
        {'mass_kg': 100, 'name': 'Hydrogen'},
        {'mass_kg': 200, 'name': 'Oxygen'}
    ]
    total_mined_mass = 250
    commodity_values = {
        'hydrogen': 10,  # Example values
        'oxygen': 20
    }

    # Example usage of select_elements
    selected_elements = select_elements(["gold", "platinum", "iron"])
    logging.info(f"Selected elements: {selected_elements}")

    # Example usage of sell_elements
    elements_sold = sell_elements(50, sample_elements, commodity_values)
    logging.info(f"Elements sold: {elements_sold}")

    # Example usage of find_elements_use
    elements_by_use = find_elements_use(sample_elements, total_mined_mass)
    logging.info(f"Elements by use: {elements_by_use}")
    pprint(elements_by_use)