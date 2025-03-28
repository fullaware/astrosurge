# Asteroid Mining Operation Simulator API Table of Contents

## API Endpoints

### Asteroid Routes (`asteroid_routes.py`)
- **`GET /asteroids/`**
  - Description: Lists all asteroids or filters by maximum distance.
  - Query Parameters:
    - `max_distance` (float, optional): The maximum distance in days.
  - Returns: A list of asteroids.

- **`GET /asteroids/{name}`**
  - Description: Retrieves details of an asteroid by its name.
  - Path Parameters:
    - `name` (str): The name of the asteroid.
  - Returns: The asteroid details.

- **`GET /asteroids/{name}/value`**
  - Description: Retrieves the estimated value of an asteroid by its name.
  - Path Parameters:
    - `name` (str): The name of the asteroid.
  - Returns: The estimated value of the asteroid.

---

### Ship Routes (`ship_routes.py`)
- **`POST /ships/`**
  - Description: Creates a new ship for a user.
  - Body Parameters:
    - `user_id` (str): The user ID.
    - `name` (str): The name of the ship.
  - Returns: The created ship.

- **`GET /ships/`**
  - Description: Lists all ships for a specific user.
  - Query Parameters:
    - `user_id` (str): The user ID.
  - Returns: A list of ships.

- **`GET /ships/{ship_id}`**
  - Description: Retrieves details of a specific ship by its ID.
  - Path Parameters:
    - `ship_id` (str): The ship ID.
  - Returns: The ship details.

- **`PUT /ships/{ship_id}`**
  - Description: Updates attributes of a specific ship.
  - Path Parameters:
    - `ship_id` (str): The ship ID.
  - Body Parameters:
    - `updates` (dict): The attributes to update.
  - Returns: The updated ship.

- **`GET /ships/{ship_id}/cargo`**
  - Description: Lists the cargo of a specific ship.
  - Path Parameters:
    - `ship_id` (str): The ship ID.
  - Returns: The list of cargo items.

- **`DELETE /ships/{ship_id}/cargo`**
  - Description: Empties the cargo of a specific ship.
  - Path Parameters:
    - `ship_id` (str): The ship ID.
  - Returns: A success message.

- **`POST /ships/{ship_id}/repair`**
  - Description: Repairs a specific ship.
  - Path Parameters:
    - `ship_id` (str): The ship ID.
  - Returns: The repaired ship and the cost of repairs.

---

### Mission Routes (`mission_routes.py`)
- **`GET /missions/`**
  - Description: Lists all missions for a specific user.
  - Query Parameters:
    - `user_id` (str): The user ID.
  - Returns: A list of missions.

- **`POST /missions/`**
  - Description: Creates a new mission for a user.
  - Body Parameters:
    - `user_id` (str): The user ID.
    - `asteroid_name` (str): The name of the asteroid.
    - `ship_id` (str): The ship ID.
    - `mining_days` (int): The number of days allocated for mining.
  - Returns: The created mission.

- **`POST /missions/{mission_id}/fund`**
  - Description: Funds a mission.
  - Path Parameters:
    - `mission_id` (str): The mission ID.
  - Returns: The funded mission.

- **`PUT /missions/{mission_id}`**
  - Description: Updates an existing mission.
  - Path Parameters:
    - `mission_id` (str): The mission ID.
  - Body Parameters:
    - `updates` (dict): The attributes to update.
  - Returns: A success message.

- **`GET /missions/{mission_id}`**
  - Description: Retrieves details of a specific mission.
  - Path Parameters:
    - `mission_id` (str): The mission ID.
  - Returns: The mission details.

---

### Simulation Routes (`simulation_routes.py`)
- **`POST /simulation/{mission_id}/start`**
  - Description: Starts a mining simulation for a specific mission.
  - Path Parameters:
    - `mission_id` (str): The mission ID.
  - Returns: A success message.

- **`GET /simulation/{mission_id}/progress`**
  - Description: Retrieves the progress of a mining simulation.
  - Path Parameters:
    - `mission_id` (str): The mission ID.
  - Returns: The simulation progress.

- **`POST /simulation/{mission_id}/stop`**
  - Description: Stops a mining simulation for a specific mission.
  - Path Parameters:
    - `mission_id` (str): The mission ID.
  - Returns: A success message.

---

### Element Routes (`element_routes.py`)
- **`GET /elements/`**
  - Description: Lists all valid elements.
  - Returns: A list of valid elements.

- **`POST /elements/select`**
  - Description: Selects elements by name.
  - Body Parameters:
    - `element_names` (list): A list of element names to select.
  - Returns: The selected elements.

- **`POST /elements/sell`**
  - Description: Sells a percentage of elements in the cargo.
  - Body Parameters:
    - `percentage` (int): The percentage of each element to sell.
    - `cargo_list` (list): The list of elements in the cargo.
    - `commodity_values` (dict): The dictionary of commodity values.
  - Returns: The sold elements and their total value.

---

### User Routes (`user_routes.py`)
- **`POST /users/login`**
  - Description: Authenticates or creates a user.
  - Body Parameters:
    - `username` (str): The username of the user.
    - `password` (str): The password of the user.
  - Returns: The user ID if authentication is successful.

- **`PUT /users/{user_id}`**
  - Description: Updates user details.
  - Path Parameters:
    - `user_id` (str): The user ID.
  - Body Parameters:
    - `updates` (dict): The attributes to update.
  - Returns: A success message and the updated user details.

- **`GET /users/{username}`**
  - Description: Retrieves the user ID by username.
  - Path Parameters:
    - `username` (str): The username of the user.
  - Returns: The username and user ID.

---

## Notes
- **All numerical values should be stored as `bson.Int64` or `$numberLong` in MongoDB to handle large numbers safely.**
- **All `_id` fields should be treated as `bson.ObjectId`.**

---

## API Routes

- [x] `asteroid_routes.py`: Endpoints for asteroid-related operations.
- [x] `ship_routes.py`: Endpoints for ship-related operations.
- [x] `mission_routes.py`: Endpoints for mission-related operations.
- [x] `simulation_routes.py`: Endpoints for running mining simulations.
- [x] `user_routes.py`: Endpoints for user authentication and updates.
- [x] `element_routes.py`: Endpoints for element selection and selling.

### Documentation

- [x] Add API documentation:
  - [x] Document all API endpoints with request/response examples.
  - [x] Include Swagger UI instructions.
- [ ] Add deployment documentation:
  - [ ] Document environment setup.
  - [ ] Document deployment steps.

### Testing

- [ ] Test all API endpoints using Swagger UI or Postman.
- [ ] Write automated tests for all API endpoints.
- [ ] Test MongoDB queries for all services.
- [ ] Verify logging to stdout and file.

### Deployment

- [ ] Add deployment instructions to `docs/`.
- [ ] Ensure `.env` is properly configured for production.
- [ ] Test deployment on a staging server.