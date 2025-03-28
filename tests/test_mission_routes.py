import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_missions():
    response = client.get("/missions/?user_id=64a7f9e2b3c2a5d6e8f9a1b2")
    assert response.status_code == 200
    assert "missions" in response.json()

def test_create_mission():
    response = client.post("/missions/", json={
        "user_id": "64a7f9e2b3c2a5d6e8f9a1b2",
        "asteroid_name": "1 Ceres",
        "ship_id": "64a7f9e2b3c2a5d6e8f9a1b3",
        "mining_days": 10
    })
    assert response.status_code == 200
    assert "mission" in response.json()

def test_fund_mission():
    mission_id = "64a7f9e2b3c2a5d6e8f9a1b4"
    response = client.post(f"/missions/{mission_id}/fund")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "message" in response.json()