import logging
import mine_asteroid
import find_asteroids
import find_elements
import update_leaderboard
import find_value
from pprint import pprint

# Find asteroids
distance = 20
total_count, asteroid_list = find_asteroids.find_asteroids(distance, distance, 1)
asteroid_name = asteroid_list[0]['full_name']
uid = "Brandon"
extraction_rate = 1000  # Set the maximum extraction rate
mine_asteroid.log(f"Total asteroids within {distance} days: {total_count}", logging.INFO)
asteroid_value = find_value.assess_asteroid_value(asteroid_name)
mine_asteroid.log(f"Retrieving asteroid info for {asteroid_name}", logging.INFO)
asteroid = mine_asteroid.get_asteroid_by_name(asteroid_name)
mine_asteroid.log(f"Asteroid value: {asteroid_value:,}", logging.INFO)
mine_asteroid.log(f"Asteroid mass before mining: {asteroid['mass']:,} kg", logging.INFO)
mine_asteroid.log(f"Mining asteroid... {asteroid_name}", logging.INFO)
asteroid, total_elements_mined = mine_asteroid.mine_asteroid(asteroid, extraction_rate, uid)

mine_asteroid.log(f"Asteroid mass after mining: {asteroid['mass']} kg", logging.INFO)
mine_asteroid.log(f"Your uid : {asteroid['uid']}", logging.INFO)
mine_asteroid.log(f"Total elements mined from this asteroid : {asteroid['mined_elements_kg']} kg", logging.INFO)

# Uncomment the following line to update the asteroid in the database
mine_asteroid.update_asteroid(asteroid)

# Find elements by use
elements_by_use = find_elements.find_elements(asteroid['elements'], asteroid['mined_elements_kg'])
mine_asteroid.log(f"Usecases supported : {elements_by_use}", logging.INFO)

# Update leaderboard
update_leaderboard.update_leaderboard(uid, asteroid['elements'], asteroid['mined_elements_kg'])

