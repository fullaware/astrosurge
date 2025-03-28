"""
main.py

This module serves as the entry point for managing asteroid mining missions. The primary objectives are:

1. **Find an Asteroid**:
   - Locate an asteroid using its name or distance from Earth.
   - Assess its value and plan a mission to mine its resources.

2. **Plan a Mission**:
   - Create a mission to mine the asteroid, assigning a ship and calculating costs.
   - Define the planned duration and investment required for the mission.

3. **Execute the Mission**:
   - Simulate the mission day by day using `execute_mining_mission`.
   - Follow the mission plan:
     a. Travel to the asteroid by incrementing or decrementing `ship.location` until it matches the asteroid's distance.
     b. Mine the asteroid by removing `mass_kg` from its elements and depositing them into the ship's cargo.
     c. Travel back to Earth by updating `ship.location` until it reaches `0` (Earth).
     d. Deposit the mined resources into the mission's `mined_elements` list.

4. **Sell Resources**:
   - Once the ship returns to Earth, sell the mined elements and update the user's/company's `bank` field with the proceeds.

5. **Track Mission Progress**:
   - Maintain the state of the mission by updating the `mission` document and `ship` variables daily.
   - Track the `actual_duration` of the mission and calculate additional costs incurred each day.

6. **Mission Completion**:
   - A mission is marked as "Mission Success" if the ship completes the trip and deposits its cargo on Earth.
   - A mission is marked as "Mission Failure" if the ship's `hull` reaches `0` before returning to Earth.

This module ensures that the mining process is realistic and adheres to the planned objectives, allowing for iterative execution of missions while maintaining accurate state tracking.
"""

from fastapi import FastAPI
from api.routes import register_routes
from config.logging_config import LoggingConfig

# Initialize logging
LoggingConfig.setup_logging()

# Create the FastAPI app
app = FastAPI(
    title="Asteroid Mining Simulator API",
    description="An API for managing asteroid mining missions, ships, and simulations.",
    version="1.0.0",
)

# Register API routes
register_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)