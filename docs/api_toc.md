# Asteroid Mining Operation Simulator API Table of Contents

## Modules and Functions

### find_asteroids.py
- **find_by_full_name(full_name: str) -> dict**
  - Description: Finds an asteroid by its full name.
  - Parameters:
    - `full_name` (str): The full name of the asteroid.
  - Returns: The asteroid data if found, otherwise None.

- **find_by_distance(moid_days: int, num_asteroids: int = 3) -> tuple**
  - Description: Finds asteroids within a specified range of moid days.
  - Parameters:
    - `moid_days` (int): The moid in days.
    - `num_asteroids` (int): The number of random asteroids to return.
  - Returns: The total count of matching asteroids and a list of randomly selected asteroids.

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
- **mine_hourly(asteroid: dict, extraction_rate: int, user_id: ObjectId) -> (dict, list)**
  - Description: Simulates extracting material from an asteroid over 1 hour.
  - Parameters:
    - `asteroid` (dict): The asteroid document.
    - `extraction_rate` (int): The maximum extraction rate.
    - `user_id` (ObjectId): The user ID.
  - Returns: The updated asteroid document and a list of elements mined.

- **update_mined_asteroid(asteroid: dict, mined_mass: int)**
  - Description: Updates the asteroid document in MongoDB with the updated elements and mass fields.
  - Parameters:
    - `asteroid` (dict): The asteroid document.
    - `mined_mass` (int): The total mined mass.
  - Returns: None.

### find_value.py
- **get_element_value(element_name: str) -> int**
  - Description: Gets the value of an element by its name.
  - Parameters:
    - `element_name` (str): The name of the element.
  - Returns: The value of the element.

### manage_users.py
- **update_users(user_id: ObjectId, elements: list)**
  - Description: Updates the users collection with the mined elements and increments the mined value.
  - Parameters:
    - `user_id` (ObjectId): The user ID.
    - `elements` (list): The list of elements mined.
  - Returns: None.

- **get_user(name: str, password: str) -> ObjectId**
  - Description: Gets or creates a user with the given name and password. If the user exists, returns the existing user ID. Otherwise, creates a new user with the specified name and password, and a bank balance of 0, and returns the new user ID.
  - Parameters:
    - `name` (str): The name of the user.
    - `password` (str): The password of the user.
  - Returns: The user ID.

- **auth_user(user_id: ObjectId, password: str) -> bool**
  - Description: Authenticates a user with the given user ID and password.
  - Parameters:
    - `user_id` (ObjectId): The user ID.
    - `password` (str): The password to authenticate.
  - Returns: True if authentication is successful, False otherwise.

- **get_user_id_by_user_name(user_name: str) -> ObjectId**
  - Description: Gets the user ID of a user by their user name.
  - Parameters:
    - `user_name` (str): The user name.
  - Returns: The user ID, or None if not found.

### manage_companies.py
- **create_company(user_id: ObjectId, company_name: str) -> bool**
  - Description: Creates a company for the user with the given user ID and company name.
  - Parameters:
    - `user_id` (ObjectId): The user ID.
    - `company_name` (str): The desired company name.
  - Returns: True if the company is created successfully, False if the company name is already in use.

- **get_company_value(user_id: ObjectId) -> int**
  - Description: Calculates the total value of a user's company.
  - Parameters:
    - `user_id` (ObjectId): The user ID.
  - Returns: The total value of the company.

- **rank_companies() -> list**
  - Description: Ranks companies based on their total value and elements mined.
  - Parameters: None.
  - Returns: A list of companies ranked by their total value and elements mined.

- **get_user_id_by_company_name(company_name: str) -> ObjectId**
  - Description: Gets the user ID of a user by their company name.
  - Parameters:
    - `company_name` (str): The company name.
  - Returns: The user ID, or None if not found.

### manage_ships.py
- **create_ship(name: str, user_id: ObjectId) -> dict**
  - Description: Creates a new ship with the given name and associates it with the user ID.
  - Parameters:
    - `name` (str): The name of the ship.
    - `user_id` (ObjectId): The user ID.
  - Returns: The created ship document or the existing ship document if it already exists.

- **get_ship(ship_id: ObjectId) -> dict**
  - Description: Retrieves a single ship by its ID.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
  - Returns: The ship document.

- **get_ships_by_user_id(user_id: ObjectId) -> list**
  - Description: Retrieves all ships associated with a given user ID.
  - Parameters:
    - `user_id` (ObjectId): The user ID.
  - Returns: A list of ship documents.

- **update_ship(ship_id: ObjectId, updates: dict) -> dict**
  - Description: Updates the attributes of a ship.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
    - `updates` (dict): The dictionary of attributes to update.
  - Returns: The updated ship document.

- **update_days_in_service(ship_id: ObjectId) -> dict**
  - Description: Updates the days in service for a ship by incrementing it by 1 day.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
  - Returns: The updated ship document.

- **update_ship_cargo(ship_id: ObjectId, cargo_list: list) -> dict**
  - Description: Updates the ship's cargo by incrementing the mass of existing elements or adding new ones.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
    - `cargo_list` (list): A list of cargo items to update, where each item is a dictionary with `name` and `mass_kg`.
  - Returns: The updated ship document.

- **list_cargo(ship_id: ObjectId) -> list**
  - Description: Lists the cargo of a ship.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
  - Returns: The list of cargo items.

- **empty_cargo(ship_id: ObjectId)**
  - Description: Empties the cargo of a ship.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
  - Returns: None.

- **repair_ship(ship_id: ObjectId) -> Int64**
  - Description: Repairs the ship and calculates the cost based on the hull damage.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
  - Returns: The cost to repair the ship as an `Int64`.

- **check_ship_status(ship_id: ObjectId)**
  - Description: Checks the status of a ship and updates it to 'inactive' if the hull is 0.
  - Parameters:
    - `ship_id` (ObjectId): The ship ID.
  - Returns: None.

### manage_mission.py
- **get_missions(user_id: ObjectId) -> list**
  - Description: Retrieves all missions for a given user ID.
  - Parameters:
    - `user_id` (ObjectId): The user ID.
  - Returns: A list of `Mission` objects.

- **plan_mission(user_id: ObjectId, asteroid_name: str, ship_cost: int = 150_000_000, operational_cost_per_day: int = 50_000) -> Mission**
  - Description: Plans a mission to mine an asteroid and saves it to the MongoDB `missions` collection.
  - Parameters:
    - `user_id` (ObjectId): The user ID planning the mission.
    - `asteroid_name` (str): The name of the asteroid.
    - `ship_cost` (int): The cost of the ship for the mission (default: $150,000,000).
    - `operational_cost_per_day` (int): The operational cost per day for the mission (default: $50,000).
  - Returns: A `Mission` object representing the planned mission.

- **fund_mission(mission_id: ObjectId, user_id: ObjectId, amount: int) -> bool**
  - Description: Funds a mission and updates its status to `FUNDED` if the funding is sufficient.
  - Parameters:
    - `mission_id` (ObjectId): The mission ID.
    - `user_id` (ObjectId): The user ID funding the mission.
    - `amount` (int): The amount to fund.
  - Returns: `True` if the mission was successfully funded, `False` otherwise.

---

### execute_mission.py
- **execute_mission(mission_id: ObjectId) -> bool**
  - Description: Executes a mission by simulating travel, mining, and returning to Earth.
  - Parameters:
    - `mission_id` (ObjectId): The mission ID.
  - Returns: `True` if the mission was successfully executed, `False` otherwise.

---

## Notes
- **All numerical values should be stored as `bson.Int64` or `$numberLong` in MongoDB to handle large numbers safely.**
- **All `_id` fields should be treated as `bson.ObjectId`.**