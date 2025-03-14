import math
import uuid
import json
import os
import random
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from the environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB client
mongodb_client = MongoClient(MONGODB_URI)

# Specify the database and collection
db = mongodb_client["asteroids"]  # Replace with your actual database name
asteroids_collection = db["asteroids"]

def get_list_of_asteroids():
    """
    This function retrieves a list of asteroid full names from MongoDB.
    """
    return asteroids_collection.find({}, {"full_name": 1, "_id": 0})

def get_asteroid_by_name(asteroid_name: str) -> dict:
    """
    This function retrieves an asteroid document from MongoDB by its full name.
    """
    query = [
    {
        '$match': {
            'full_name': asteroid_name
        }
    }, {
        '$lookup': {
            'from': 'elements', 
            'localField': 'class', 
            'foreignField': 'classes.class', 
            'as': 'results'
        }
    }, {
        '$project': {
            'full_name': 1, 
            'diameter': 1, 
            'class': 1, 
            'moid': 1, 
            'elements': 1, 
            'results.name': 1,
            'results.number': 1, 
            'results.classes.class': 1, 
            'results.classes.percentage': 1
        }
    }
    ]
    return list(asteroids_collection.aggregate(query))[0]

def update_asteroid_elements(asteroid_name: str, elements: list, moid_days: int, mass: int, synthetic: bool = False):
    """
    This function updates the asteroid document in MongoDB with the elements field, moid_days field, mass field, and synthetic field.
    Each element includes its name, number, and mass in kg.
    """
    # Ensure mass does not exceed the maximum limit for 8-byte integers
    max_int_8_byte = 2**63 - 1
    if mass > max_int_8_byte:
        mass = max_int_8_byte

    update_fields = {"elements": elements, "moid_days": moid_days, "mass": mass}
    if synthetic:
        update_fields["synthetic"] = True

    asteroids_collection.update_one(
        {"full_name": asteroid_name},
        {"$set": update_fields}
    )

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

def convert_diameter_to_mass(diameter: float, asteroid_class: str) -> int:
    """
    This function is responsible for converting the diameter of the asteroid to its mass in kilograms.
    The asteroid_class parameter determines the density:
    - 'C' class: 1.38 g/cm^3
    - 'S' class: 2.71 g/cm^3
    - 'M' class: 5.32 g/cm^3
    """
    # Convert diameter from km to meters
    diameter = diameter * 1000
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

def calculate_element_mass(useful_mass: int, percentage: float, total_percentage: float) -> int:
    """
    This function calculates the mass of an element in the asteroid.
    The element has a certain percentage chance of appearing in the asteroid.
    The total percentage of all elements is used to ensure the total mass does not exceed 10% of the asteroid's mass.
    """
    adjusted_percentage = percentage / total_percentage
    element_mass = useful_mass * adjusted_percentage
    return round(element_mass)

# Initialize counter for updated asteroids
updated_count = 0

# Fetch all asteroids from the collection
asteroids = get_list_of_asteroids()

# Iterate over each asteroid in the collection
for asteroid in asteroids:
    asteroid_elements = get_asteroid_by_name(asteroid['full_name'])
    asteroid_class = asteroid_elements.get('class')
    moid = asteroid_elements.get('moid')
    diameter = asteroid_elements.get('diameter')

    synthetic = False
    if diameter is None:
        diameter = random.uniform(1, 500)
        synthetic = True

    if moid is None:
        moid = random.uniform(1e-5, 1)
        synthetic = True

    # Validate asteroid class and assign a random class if necessary
    if asteroid_class not in ['C', 'S', 'M']:
        asteroid_class = random.choice(['C', 'S', 'M'])  # Assign a random class if missing or invalid
        synthetic = True

    # Convert diameter to mass
    mass = convert_diameter_to_mass(diameter, asteroid_class)

    # Calculate the total useful mass (10% of the total mass)
    useful_mass = mass * 0.10

    # Check if 'results' key exists in the asteroid dictionary
    if 'results' in asteroid_elements:
        # Calculate the total percentage of all elements
        total_percentage = 0
        for element in asteroid_elements['results']:
            for cls in element['classes']:
                if cls['class'] == asteroid_class:
                    total_percentage += cls['percentage']

        # Initialize total mass
        total_mass = 0

        # Initialize elements list to store element details
        elements_list = []

        # Calculate the mass of each element
        for element in asteroid_elements['results']:
            for cls in element['classes']:
                if cls['class'] == asteroid_class:
                    element_mass = calculate_element_mass(useful_mass, cls['percentage'], total_percentage)
                    total_mass += element_mass
                    elements_list.append({
                        "name": element['name'],
                        "mass_kg": element_mass,
                        "number": element['number']
                    })
                    print(f"{element['name']} : {element_mass:,} kg ({cls['percentage']}%)")

        # Check if total_mass is 0
        # if total_mass == 0:
        #     raise ValueError(f"Total mass of elements is 0 for asteroid: {asteroid['full_name']}")

        # Calculate moid_days
        moid_km = convert_moid_km(moid)
        # if moid_km == 0:
        #     raise ValueError(f"MOID in kilometers is 0 for asteroid: {asteroid['full_name']}")
        moid_days = convert_km_to_days(moid_km)

        # Print the total mass of all elements
        print(f"Total mass of all elements: {total_mass:,} kg")
        print(f"Total mass of asteroid: {mass:,} kg")
        print(f"Total mass of asteroid - elements: {mass - total_mass:,} kg")
        print(f"MOID in days: {moid_days} days")

        # Update the asteroid document in MongoDB with the elements field, moid_days, mass, and synthetic if applicable
        update_asteroid_elements(asteroid['full_name'], elements_list, moid_days, mass, synthetic)
        
        # Increment the counter for updated asteroids
        updated_count += 1
    else:
        print(f"No 'results' key found for asteroid: {asteroid['full_name']}")

# Print the count of updated asteroids
print(f"Number of asteroids updated: {updated_count}")