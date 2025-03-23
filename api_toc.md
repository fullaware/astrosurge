# Space Mining Simulator API Table of Contents

## Modules and Functions

### find_asteroids.py
- **find_by_name(name: str) -> dict**
  - Description: Finds an asteroid by its name.
  - Parameters:
    - `name` (str): The name of the asteroid.
  - Returns: The asteroid data if found, otherwise None.

- **find_by_distance(max_days: float) -> list**
  - Description: Finds asteroids within a specified maximum distance in days.
  - Parameters:
    - `max_days` (float): The maximum distance in days.
  - Returns: A list of asteroids within the specified distance.

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