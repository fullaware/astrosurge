from fastapi import APIRouter, HTTPException
from amos import find_by_full_name, find_by_distance, assess_asteroid_value  # Updated import

asteroid_router = APIRouter()

@asteroid_router.get("/")
def list_asteroids(max_distance: float = None):
    """
    List all asteroids or filter by maximum distance.
    """
    if max_distance:
        asteroids = find_by_distance(max_distance)
    else:
        asteroids = find_by_distance(float("inf"))  # No limit
    return {"asteroids": asteroids}

@asteroid_router.get("/{name}")
def get_asteroid(name: str):
    """
    Get details of an asteroid by name.
    """
    asteroid = find_by_full_name(name)
    if not asteroid:
        raise HTTPException(status_code=404, detail="Asteroid not found")
    return {"asteroid": asteroid}

@asteroid_router.get("/{name}/value")
def get_asteroid_value(name: str):
    """
    Get the estimated value of an asteroid by name.
    """
    asteroid = find_by_full_name(name)
    if not asteroid:
        raise HTTPException(status_code=404, detail="Asteroid not found")
    value = assess_asteroid_value(asteroid)
    return {"name": name, "value": value}