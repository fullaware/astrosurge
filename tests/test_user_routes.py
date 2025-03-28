import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_user():
    response = client.post("/users/login", json={"username": "john_doe", "password": "securepassword123"})
    assert response.status_code == 200
    assert "user_id" in response.json()

def test_update_user():
    user_id = "64a7f9e2b3c2a5d6e8f9a1b2"
    response = client.put(f"/users/{user_id}", json={"email": "john.doe@example.com"})
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "message" in response.json()

def test_get_user_id():
    username = "john_doe"
    response = client.get(f"/users/{username}")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "user_id" in response.json()