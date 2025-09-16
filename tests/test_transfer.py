import logging
import pytest

logger = logging.getLogger(__name__)

@pytest.fixture
def create_account_with_balance(client, login_user, signup_user):
    def _create(username, password, full_name, balance):
        signup_user(username, password, full_name)
        headers = login_user(username, password)
        assert headers is not None
        response = client.post("/accounts", json={"initial_balance": balance}, headers=headers)
        assert response.status_code == 200
        return client, headers
    return _create

def test_external_transfer_flow(create_account_with_balance):
    username = "external_user"
    password = "testpassword123"
    full_name = "External User"
    client, headers = create_account_with_balance(username, password, full_name, 1000.0)

    # Get account id
    response = client.get("/accounts", headers=headers)
    assert response.status_code == 200
    accounts = response.json().get("accounts", [])
    assert accounts
    account_id = accounts[0]["id"]

    # Valid transfer
    valid_data = {"from_account_id": account_id, "external_account": "EXTERNAL12345678", "amount": 100.0}
    r = client.post("/external-transfer", json=valid_data, headers=headers)
    assert r.status_code == 200
    assert r.json().get("message") == "External transfer successful"

    # Negative amount
    invalid_data = valid_data.copy()
    invalid_data["amount"] = -10.0
    r = client.post("/external-transfer", json=invalid_data, headers=headers)
    assert r.status_code == 400

    # Amount exceeds limit (e.g. 10000)
    invalid_data["amount"] = 10000.0
    r = client.post("/external-transfer", json=invalid_data, headers=headers)
    assert r.status_code == 400

    # Insufficient funds (very large amount)
    invalid_data["amount"] = 999999.0
    r = client.post("/external-transfer", json=invalid_data, headers=headers)
    assert r.status_code == 400
