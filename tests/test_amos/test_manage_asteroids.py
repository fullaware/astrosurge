from amos import find_by_full_name, find_by_distance

def test_find_by_full_name():
    asteroid_name = "1 Ceres"
    asteroid = find_by_full_name(asteroid_name)
    assert asteroid is None or asteroid["full_name"] == asteroid_name

def test_find_by_distance():
    max_distance = 10.0
    asteroids = find_by_distance(max_distance)
    assert isinstance(asteroids, list)
    for asteroid in asteroids:
        assert asteroid["distance"] <= max_distance