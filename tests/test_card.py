import logging
import pytest
from app.database import get_db

logger = logging.getLogger(__name__)

@pytest.fixture
def create_account(client, login_user, signup_user):
    def _create_account(username, password, full_name, initial_balance=1000.0):
        signup_user(username, password, full_name)
        headers = login_user(username, password)
        assert headers is not None
        response = client.post("/accounts", json={"initial_balance": initial_balance}, headers=headers)
        assert response.status_code == 200
        return client, headers
    return _create_account

def test_card_lifecycle(create_account):
    username = "card_test_user"
    password = "CardPass123!"
    full_name = "Card Test User"
    client, headers = create_account(username, password, full_name)

    # List accounts to get account_id
    response = client.get("/accounts", headers=headers)
    assert response.status_code == 200
    accounts = response.json().get("accounts", [])
    assert accounts
    account_id = accounts[0]["id"]

    # Create card
    card_data = {"account_id": account_id, "card_type": "debit", "expiry": "12/30"}
    response = client.post("/cards", json=card_data, headers=headers)
    assert response.status_code == 200
    card_number = response.json()["card_number"]

    # Fetch card_id from DB
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cards WHERE card_number = ?", (card_number,))
        card = cursor.fetchone()
    finally:
        conn.close()
    assert card is not None
    card_id = card["id"]

    # Update card status
    response = client.put(f"/cards/{card_id}/status", json={"status": "blocked"}, headers=headers)
    assert response.status_code == 200

    # Update card PIN
    response = client.put(f"/cards/{card_id}/pin", json={"pin": "4321"}, headers=headers)
    assert response.status_code == 200

    # Delete card
    response = client.delete(f"/cards/{card_id}", headers=headers)
    assert response.status_code == 200
