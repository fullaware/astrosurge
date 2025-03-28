import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_asteroids():
    response = client.get("/asteroids/")
    assert response.status_code == 200
    assert "asteroids" in response.json()

def test_get_asteroid():
    asteroid_name = "Ceres"
    response = client.get(f"/asteroids/{asteroid_name}")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "asteroid" in response.json()

def test_get_asteroid_value():
    asteroid_name = "Ceres"
    response = client.get(f"/asteroids/{asteroid_name}/value")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "value" in response.json()