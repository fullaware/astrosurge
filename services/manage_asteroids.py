from config.mongodb_config import MongoDBConfig

asteroids_collection = MongoDBConfig.get_collection("asteroids")

def find_by_full_name(name: str):
    return asteroids_collection.find_one({"full_name": name})

def find_by_distance(max_distance: float):
    return list(asteroids_collection.find({"distance": {"$lte": max_distance}}))

def assess_asteroid_value(asteroid: dict):
    resources = asteroid.get("resources", [])
    return sum(resource["value"] * resource["mass"] for resource in resources)