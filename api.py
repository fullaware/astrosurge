# Build all API endpoints for use in simulating traveling to an asteroid, mining it, and returning to Earth with the mined resources.  
# The API should include the following endpoints:
# Each user will have a unique identifier (uid) that is a string to allow for multiple simultaneous users.

import math
import uuid
import json

def get_asteroid_data():
    """
    This function is responsible for fetching the asteroid data from MongoDB.
    """
    data = mongodb_client.db["asteroids"].collection["asteroids"].find()
    return data

def convert_moid_km(moid: str) -> float:
    """
    This function is responsible for converting the Minimum Orbit Intersection Distance (MOID) from astronomical units to kilometers.
    """
    return float(moid) * 149597870.7

def convert_km_to_days(km: int) -> int:
    """
    This function is responsible for converting the distance in kilometers to travel days.  
    Based on travel from Earth to Mars in 45 days.
    https://www.iflscience.com/nuclear-thermal-propulsion-reactor-fuel-that-could-take-humans-to-mars-tested-at-nasa-facility-77719 
    The distance from Earth to Mars is 0.52 AU or 78,340,000 km. 
    `78,340,000 km / 45 days = 1,740,889 km per day`
    """
    return int(km / 1740889)

def convert_diameter_to_mass(diameter: str, asteroid_class: str) -> int:
    """
    This function is responsible for converting the diameter of the asteroid to its mass in kilograms.
    The asteroid_class parameter determines the density:
    - 'C' class: 1.38 g/cm^3
    - 'S' class: 2.71 g/cm^3
    - 'M' class: 5.32 g/cm^3
    """
    diameter = float(diameter)
    # Assuming the asteroid is spherical
    radius = diameter / 2
    volume = (4 / 3) * math.pi * (radius ** 3)
    
    # Determine the density based on the asteroid class
    if asteroid_class == 'C':
        density = 1.38
    elif asteroid_class == 'S':
        density = 2.71
    elif asteroid_class == 'M':
        density = 5.32
    else:
        raise ValueError("Invalid asteroid class. Use 'C', 'S', or 'M'.")
    
    # Convert density from g/cm^3 to kg/m^3
    density_kg_m3 = density * 1000
    
    mass = volume * density_kg_m3
    return int(mass)

def calculate_element_mass(mass: int, percentage: float) -> int:
    """
    This function calculates the mass of an element in the asteroid.
    The element has a certain percentage chance of appearing in the asteroid.
    Only 10% of the mass is useful, as 90% is useless rock.
    """
    useful_mass = mass * 0.10
    element_mass = useful_mass * (percentage / 100)
    return round(element_mass)

api_schema = {
"uid": uuid.uuid4(),
"shield": "INT shield strength maxes out at 100",
"day": "INT day tracker, increment by 1 each day",
"asteroid_found": "BOOL true or false",
"asteroid_mass": "INT in kg",
"asteroid_travel_days": "INT",
"ship_cargo": "INT Maximum cargo capacity 10,000 kg",
"earth_distance": "INT distance from earth in days",  
"travel_days_left": "INT distance from ship to destination" 
}

mission_schema = {
"uid": uuid.uuid4(),
"day": "INT day tracker, increment by 1 each day",
"asteroid_mass": "INT in kg",  # sys.maxsize = 9,223,372,036,854,775,807
"asteroid_travel_days": "INT",
"ship_cargo": "INT Maximum cargo capacity 10,000 kg",
"earth_distance": "INT distance from earth in days",
"travel_days_left": "INT distance from ship to destination",
"extraction_rate": "INT amount of material extracted per day",
"cargo": "INT amount of material in cargo",
"total_days": "INT total days of mission",
"total_material": "INT total material extracted",
"total_distance": "INT total distance traveled"
}

mongodb_query_find_elements_by_class = [
    {
        '$match': {
            'name': 'Ceres'
        }
    }, {
        '$lookup': {
            'from': 'elements', 
            'localField': 'class', 
            'foreignField': 'classes.class', 
            'as': 'elements'
        }
    }, {
        '$project': {
            'name': 1, 
            'class': 1,
            'diameter': 1,
            'moid': 1,
            'elements.name': 1, 
            'elements.classes.class': 1, 
            'elements.classes.percentage': 1
        }
    }
]

# Read the contents of the results.json file
with open('results.json', 'r') as file:
    mongodb_query_find_elements_by_class_result = json.load(file)

# Extract class, moid, and diameter
if mongodb_query_find_elements_by_class_result:
    asteroid_class = mongodb_query_find_elements_by_class_result[0]['class']
    moid = mongodb_query_find_elements_by_class_result[0]['moid']
    diameter = mongodb_query_find_elements_by_class_result[0]['diameter']

    # Convert diameter to mass
    mass = convert_diameter_to_mass(diameter, asteroid_class)

    # Calculate the mass of each element
    for element in mongodb_query_find_elements_by_class_result[0]['elements']:
        for cls in element['classes']:
            if cls['class'] == asteroid_class:
                element_mass = calculate_element_mass(mass, cls['percentage'])
                print(f"{element['name']} : {element_mass} kg")
else:
    print("No data found in mongodb_query_find_elements_by_class_result")