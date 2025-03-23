# Asteroid Mining Operation Simulator API Table of Contents

## Modules and Functions

### find_asteroids.py
- **find_by_name(name: str) -> dict**
  - Description: Finds an asteroid by its name.
  - Parameters:
    - `name` (str): The name of the asteroid.
  - Returns: The asteroid data if found, otherwise None.

- **find_by_distance(min_distance_days: int, max_distance_days: int, num_asteroids: int = 3) -> tuple**
  - Description: Finds asteroids within a specified range of minimum and maximum distance days.
  - Parameters:
    - `min_distance_days` (int): The minimum distance in days.
    - `max_distance_days` (int): The maximum distance in days.
    - `num_asteroids` (int): The number of random asteroids to return.
  - Returns: A tuple containing the total count of matching asteroids and a list of randomly selected asteroids.

### manage_elements.py
- **select_elements(user_choice=None) -> list**
  - Description: Selects elements to mine based on user input or predefined criteria.
  - Parameters:
    - `user_choice` (list, optional): A list of user-selected elements.
  - Returns: A list of valid elements to mine.

- **find_elements_use(elements: list, total_mined_mass: int) -> list**
  - Description: Processes the elements and categorizes them by their use.
  - Parameters:
    - `elements` (list): The list of elements.
    - `total_mined_mass` (int): The total mined mass.
  - Returns: A list of elements categorized by use and their total mass.

- **sell_elements(percentage: int, cargo_list: list, commodity_values: dict) -> dict**
  - Description: Sells a percentage of each element in the cargo list.
  - Parameters:
    - `percentage` (int): The percentage of each element to sell.
    - `cargo_list` (list): The list of elements in the cargo.
    - `commodity_values` (dict): The dictionary of commodity values.
  - Returns: A dictionary of elements with their total value.

### mine_asteroid.py
- **mine_hourly(asteroid: dict, extraction_rate: int, uid: str) -> (dict, list)**
  - Description: Simulates extracting material from an asteroid over 1 hour.
  - Parameters:
    - `asteroid` (dict): The asteroid document.
    - `extraction_rate` (int): The maximum extraction rate.
    - `uid` (str): The user ID.
  - Returns: The updated asteroid document and a list of elements mined.

- **update_mined_asteroid(asteroid: dict, mined_mass: int)**
  - Description: Updates the asteroid document in MongoDB with the updated elements and mass fields.
  - Parameters:
    - `asteroid` (dict): The asteroid document.
    - `mined_mass` (int): The total mined mass.
  - Returns: None.

## Notes
- **All numerical values should be stored as `INT64` or `$numberLong` in MongoDB to handle large numbers safely.**