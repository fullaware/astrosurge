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