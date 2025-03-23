"""
Asteroid Mining Operation Simulator Project Structure

1. find_asteroids.py
   - Retrieves asteroids by name or distance (moid_days).
"""

from find_asteroids import find_by_name, find_by_distance

def main():
    print("Starting the Asteroid Mining Operation Simulator MVP...")
    
    # Step 1: Select asteroid
    min_distance_days = 1
    max_distance_days = 10
    num_asteroids = 3
    total_count, asteroids = find_by_distance(min_distance_days, max_distance_days, num_asteroids)
    print(f"Total count of matching asteroids: {total_count}")
    print("Randomly selected asteroids:")
    for asteroid in asteroids:
        print(asteroid)
    
    if not asteroids:
        print("No asteroids found in the specified range.")
        return
    
    asteroid = asteroids[0]  # Select the first asteroid from the list
    print(f"Selected asteroid: {asteroid}")

if __name__ == "__main__":
    main()
