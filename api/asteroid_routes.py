from fastapi import APIRouter, HTTPException
from amos import find_by_full_name, find_by_distance, assess_asteroid_value

asteroid_router = APIRouter()

@asteroid_router.get("/", response_model=dict)
def list_asteroids(max_distance: float = None):
    """
    List all asteroids or filter by maximum distance.

    - **max_distance**: The maximum distance (in days) to filter asteroids.
    - **Returns**: A dictionary containing a list of asteroids.
    """
    if max_distance:
        asteroids = find_by_distance(max_distance)
    else:
        asteroids = find_by_distance(float("inf"))  # No limit
    return {"asteroids": asteroids}

@asteroid_router.get("/{name}", response_model=dict)
def get_asteroid(name: str):
    """
    Get details of an asteroid by name.

    - **name**: The name of the asteroid.
    - **Returns**: A dictionary containing the asteroid details.
    """
    asteroid = find_by_full_name(name)
    if not asteroid:
        raise HTTPException(status_code=404, detail="Asteroid not found")
    return {"asteroid": asteroid}

@asteroid_router.get("/{name}/value", response_model=dict)
def get_asteroid_value(name: str):
    """
    Get the estimated value of an asteroid by name.

    - **name**: The name of the asteroid.
    - **Returns**: A dictionary containing the asteroid name and its estimated value.
    """
    asteroid = find_by_full_name(name)
    if not asteroid:
        raise HTTPException(status_code=404, detail="Asteroid not found")
    value = assess_asteroid_value(asteroid)
    return {"name": name, "value": value}