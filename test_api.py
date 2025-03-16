import logging
from pprint import pprint
import find_asteroids
import find_value
import mine_asteroid
import manage_ship
import manage_elements

# Configure logging to show only INFO level messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Find asteroids
    distance = 20
    total_count, asteroid_list = find_asteroids.find_asteroids(distance, distance, 1)
    asteroid_name = asteroid_list[0]['full_name']
    logging.info(f"Total asteroids within {distance} days: {total_count}")

    uid = "Brandon"  # Set the user id
    oid = "Merlin"  # Set the object id of the Ship

    extraction_rate = 1000  # Set the maximum extraction rate

    # Retrieve the asteroid document
    asteroid = mine_asteroid.get_asteroid_by_name(asteroid_name)

    # Assess the value of the asteroid
    asteroid_value = find_value.assess_asteroid_value(asteroid)
    logging.info(f"Asteroid value: {asteroid_value:,}")

    logging.info(f"Asteroid mass before mining: {asteroid['mass']:,} kg")
    logging.info(f"Mining asteroid... {asteroid_name}")
    asteroid, list_elements_mined = mine_asteroid.mine_asteroid(asteroid, extraction_rate, uid)

    logging.info(f"Asteroid mass after mining: {asteroid['mass']} kg")
    logging.info(f"Your uid : {asteroid['uid']}")
    logging.info(f"Total elements mined from this asteroid : {asteroid['mined_elements_kg']} kg")

    # Calculate the total mined mass
    mined_mass = sum([element['mass_kg'] for element in list_elements_mined])
    print(f"Total mined mass: {mined_mass} kg")
    # Update the asteroid in the database
    mine_asteroid.update_mined_asteroid(asteroid, mined_mass)

    # Find elements by use
    elements_by_use = manage_elements.find_elements_use(asteroid['elements'], asteroid['mined_elements_kg'])
    logging.info(f"Usecases supported : {elements_by_use}")

    # Update users
    total_value = find_value.assess_element_values(list_elements_mined, manage_ship.commodity_values)
    manage_elements.update_users(uid, elements=asteroid['elements'], total_mined_mass=mined_mass, total_value=total_value)
    print(f"Total_value mined : ${total_value:,}")

    # Add a new ship and update its days in service
    new_ship = manage_ship.get_ship("Merlin", uid)
    updated_ship = manage_ship.update_days_in_service(new_ship['oid'])

    # Update ship cargo with mined elements
    updated_ship = manage_ship.update_cargo(new_ship['oid'], list_elements_mined)

    # List cargo with values
    cargo_list = manage_ship.list_cargo(new_ship['oid'])
    pprint(cargo_list)

    # Assess the value of each element in the cargo
    commodity_values = manage_ship.commodity_values

    # Sell elements
    manage_elements.sell_elements(uid, 50, cargo_list, commodity_values)

if __name__ == "__main__":
    main()

