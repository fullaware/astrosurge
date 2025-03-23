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
  - Description: Manages logic around which elements to mine.
  - Parameters:
    - `user_choice` (list, optional): A list of user-selected elements.
  - Returns: A list of valid elements to mine.

### mine_asteroid.py
- **mine_hourly() -> float**
  - Description: Simulates mining yields over time.
  - Returns: The amount of material mined in kg.

### simulator.py
- **main()**
  - Description: Main function to run the Space Mining Simulator MVP.
  - Steps:
    - Select asteroid
    - Manage elements
    - Launch mission and simulate mining
    - Display results