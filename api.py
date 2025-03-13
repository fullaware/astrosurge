# Build all API endpoints for use in simulating traveling to an asteroid, mining it, and returning to Earth with the mined resources.  
# The API should include the following endpoints:
# Each user will have a unique identifier (uid) that is a string to allow for multiple simultaneous users.

def get_asteroid_data():
    """
    This function is responsible for fetching the asteroid data from MongoDB.
    """
    data = mongodb_client.db.collection.find()
    return data

def convert_moid_km(moid: str) -> float:
    """
    This function is responsible for converting the Minimum Orbit Intersection Distance (MOID) from astronomical units to kilometers.
    """
    return float(moid) * 149597870.7

def convert_km_to_days(km: float) -> int:
    """
    This function is responsible for converting the distance in kilometers to travel days.  Based on travel from Earth to Mars in 45 days.
    """
    return int(km / 10000)

def convert_diameter_to_mass(diameter: str) -> int:
    """
    This function is responsible for converting the diameter of the asteroid to its mass in kilograms.
    """
    diameter = float(diameter)
    # Assuming the asteroid is spherical
    radius = diameter / 2
    volume = (4 / 3) * math.pi * (radius ** 3)
    # Assuming the density of the asteroid is 2 g/cm^3
    mass = volume * 2 * 1000
    return int(mass)

api_schema = {
"uid": uid,
"shield": max(0, shield),
"luck": luck,
"day": "INT",
"asteroid_found": "BOOL true or false",
"asteroid_mass": "INT in kg",
"asteroid_travel_days": "INT",
"ship_cargo": "INT Maximum cargo capacity 10,000 kg",
"base_travel_days": base_travel_days,  # Persist base_travel_days
"total_travel_days": total_travel_days  # Persist total_travel_days for future reference
}