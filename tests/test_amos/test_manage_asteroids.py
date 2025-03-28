from amos.manage_asteroids import find_by_full_name, find_by_distance, assess_asteroid_value
from unittest.mock import patch
from bson import ObjectId

def test_find_by_full_name():
    asteroid_name = "1 Ceres"
    mock_asteroid = {
        "_id": ObjectId("64a7f9e2b3c2a5d6e8f9a1b2"),
        "spkid": 1,
        "full_name": "1 Ceres",
        "pdes": "Ceres",
        "name": "Ceres",
        "neo": False,
        "hazard": False,
        "abs_magnitude": 3.34,
        "diameter": 939.4,
        "albedo": 0.09,
        "diameter_sigma": 0.1,
        "orbit_id": "2023",
        "moid": 1.2,
        "moid_days": 365,
        "mass": 1000000,
        "value": 5000000,
        "elements": [{"name": "Gold", "mass_kg": 1000, "number": 79}],
    }

    with patch("amos.manage_asteroids.asteroids_collection.find_one", return_value=mock_asteroid):
        asteroid = find_by_full_name(asteroid_name)
        assert asteroid is not None
        assert asteroid.full_name == asteroid_name

def test_find_by_distance():
    max_distance = 10.0
    mock_asteroids = [
        {
            "_id": ObjectId("64a7f9e2b3c2a5d6e8f9a1b2"),
            "spkid": 1,
            "full_name": "1 Ceres",
            "pdes": "Ceres",
            "name": "Ceres",
            "neo": False,
            "hazard": False,
            "abs_magnitude": 3.34,
            "diameter": 939.4,
            "albedo": 0.09,
            "diameter_sigma": 0.1,
            "orbit_id": "2023",
            "moid": 1.2,
            "moid_days": 365,
            "mass": 1000000,
            "value": 5000000,
            "elements": [],
        },
        {
            "_id": ObjectId("64a7f9e2b3c2a5d6e8f9a1b3"),
            "spkid": 2,
            "full_name": "2 Pallas",
            "pdes": "Pallas",
            "name": "Pallas",
            "neo": False,
            "hazard": False,
            "abs_magnitude": 4.13,
            "diameter": 512.0,
            "albedo": 0.12,
            "diameter_sigma": 0.2,
            "orbit_id": "2023",
            "moid": 2.5,
            "moid_days": 730,
            "mass": 500000,
            "value": 2000000,
            "elements": [],
        },
    ]

    with patch("amos.manage_asteroids.asteroids_collection.find", return_value=mock_asteroids):
        asteroids = find_by_distance(max_distance)
        assert len(asteroids) == 2
        for asteroid in asteroids:
            assert asteroid.moid <= max_distance

def test_assess_asteroid_value():
    mock_asteroid = {
        "full_name": "1 Ceres",
        "resources": [
            {"name": "gold", "mass_kg": 1000, "value": 50000},
            {"name": "silver", "mass_kg": 500, "value": 25000},
        ],
    }
    total_value = assess_asteroid_value(mock_asteroid)
    assert total_value == 50000 * 1000 + 25000 * 500