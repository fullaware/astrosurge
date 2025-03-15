import logging
import mine_asteroid
import find_asteroids
import find_elements
import update_leaderboard
import find_value
import update_ship
from pprint import pprint

# Configure logging to show only ERROR level messages
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Find asteroids
distance = 20
total_count, asteroid_list = find_asteroids.find_asteroids(distance, distance, 1)
asteroid_name = asteroid_list[0]['full_name']
# asteroid_name = "(2018 JC3)"

uid = "Brandon" # Set the user id
oid = "Merlin" # Set the object id of the Ship

extraction_rate = 1000  # Set the maximum extraction rate
logging.info(f"Total asteroids within {distance} days: {total_count}")

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

# Update the asteroid in the database
mine_asteroid.update_asteroid(asteroid, mined_mass)

# Find elements by use
elements_by_use = find_elements.find_elements(asteroid['elements'], asteroid['mined_elements_kg'])
logging.info(f"Usecases supported : {elements_by_use}")

# Update leaderboard
update_leaderboard.update_leaderboard(uid, asteroid['elements'], asteroid['mined_elements_kg'])

# Add a new ship and update its days in service
new_ship = update_ship.get_ship("Merlin", uid)
updated_ship = update_ship.update_days_in_service(new_ship['oid'])

# Update ship cargo with mined elements
updated_ship = update_ship.update_cargo(new_ship['oid'], list_elements_mined)

# List cargo with values
cargo_list = update_ship.list_cargo(new_ship['oid'])
pprint(cargo_list)

