"""
Space Mining Simulator Project Structure

1. manage_elements.py
   - Manages logic around which elements to mine.

2. find_asteroids.py
   - Retrieves asteroids by name or distance (moid_days).

3. mine_asteroid.py
   - Simulates mining yields over time.

4. webui.py
   - A minimal FastAPI interface with dark theme placeholders.

5. templates/base.html
   - Base HTML template for the web UI.

6. templates/index.html
   - Index page template for the web UI.

7. templates/missions.html
   - Missions page template for the web UI.

8. static/css/style.css
   - Custom CSS for styling the web UI.
"""

from find_asteroids import find_by_name, find_by_distance
from manage_elements import select_elements
from mine_asteroid import mine_hourly, get_asteroid_by_name, mine_asteroid, update_mined_asteroid

def main():
    print("Starting the Space Mining Simulator MVP...")
    
    # Step 1: Select asteroid
    asteroid_name = "Alpha"
    asteroid = get_asteroid_by_name(asteroid_name)
    if not asteroid:
        print("Asteroid not found.")
        return
    
    # Step 2: Manage elements
    elements = select_elements()
    print(f"Selected elements: {elements}")
    
    # Step 3: Launch mission and simulate mining
    total_yield = 0
    for _ in range(24):  # Simulate 24 hours of mining
        total_yield += mine_hourly()
    
    # Step 4: Display results
    print(f"Total yield from mining: {total_yield:.2f} kg")
    mined_asteroid, elements_mined = mine_asteroid(asteroid, 1000, "unique_id")
    update_mined_asteroid(mined_asteroid, total_yield)
    print("Mined elements:")
    for element in elements_mined:
        print(f"{element['name']}: {element['mass_kg']} kg")

if __name__ == "__main__":
    main()
