import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_elements():
    response = client.get("/elements/")
    assert response.status_code == 200
    assert "elements" in response.json()

def test_select_elements():
    response = client.post("/elements/select", json={"element_names": ["gold", "silver"]})
    assert response.status_code == 200
    assert "selected_elements" in response.json()