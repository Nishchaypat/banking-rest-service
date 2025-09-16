import logging
import pytest

logger = logging.getLogger(__name__)

@pytest.mark.parametrize(
    "username, password, full_name",
    [
        ("test_user1", "Password123!", "Test User One"),
        ("test_user2", "Password123!", "Test User Two"),
    ],
)
def test_signup(signup_user, username, password, full_name):
    logger.info(f"Testing signup for {username}")
    response = signup_user(username, password, full_name)
    assert response.status_code in (200, 400)  # 400 if user exists

def test_login(login_user, signup_user):
    username = "login_test_user"
    password = "SecurePass456!"
    full_name = "Login Test User"
    signup_user(username, password, full_name)
    headers = login_user(username, password)
    assert headers is not None
    assert "Authorization" in headers

def test_create_account(client, login_user, signup_user):
    username = "account_test_user"
    password = "AccountPass789!"
    full_name = "Account Test User"
    signup_user(username, password, full_name)
    headers = login_user(username, password)
    assert headers is not None
    
    response = client.post("/accounts", json={"initial_balance": 100.0}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Account created successfully"
