import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def signup_user(client):
    def _signup(username, password, full_name):
        response = client.post("/signup", json={"username": username, "password": password, "full_name": full_name})
        return response
    return _signup

@pytest.fixture
def login_user(client):
    def _login(username, password):
        response = client.post("/token", data={"username": username, "password": password})
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            return headers
        else:
            return None
    return _login
