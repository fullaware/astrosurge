import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_ship():
    response = client.post("/ships/", json={"user_id": "64a7f9e2b3c2a5d6e8f9a1b2", "name": "Explorer-1"})
    assert response.status_code == 200
    assert "ship" in response.json()

def test_list_user_ships():
    response = client.get("/ships/?user_id=64a7f9e2b3c2a5d6e8f9a1b2")
    assert response.status_code == 200
    assert "ships" in response.json()

def test_get_ship_details():
    ship_id = "64a7f9e2b3c2a5d6e8f9a1b3"
    response = client.get(f"/ships/{ship_id}")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "ship" in response.json()

def test_list_ship_cargo():
    ship_id = "64a7f9e2b3c2a5d6e8f9a1b3"
    response = client.get(f"/ships/{ship_id}/cargo")
    assert response.status_code == 200
    assert "cargo" in response.json()

def test_clear_ship_cargo():
    ship_id = "64a7f9e2b3c2a5d6e8f9a1b3"
    response = client.delete(f"/ships/{ship_id}/cargo")
    assert response.status_code == 200
    assert "message" in response.json()

def test_repair_ship():
    ship_id = "64a7f9e2b3c2a5d6e8f9a1b3"
    response = client.post(f"/ships/{ship_id}/repair")
    assert response.status_code == 200
    assert "ship" in response.json()