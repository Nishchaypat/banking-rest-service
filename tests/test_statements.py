import logging
import csv
from io import StringIO
from datetime import datetime
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

def test_monthly_statements(create_account_with_balance):
    username = "statement_user"
    password = "testpassword123"
    full_name = "Statement User"
    client, headers = create_account_with_balance(username, password, full_name, 500)

    # Get account id
    response = client.get("/accounts", headers=headers)
    assert response.status_code == 200
    accounts = response.json().get("accounts", [])
    assert accounts
    account_id = accounts[0]["id"]

    # Create deposit transaction
    deposit_data = {"account_id": account_id, "type": "deposit", "amount": 100.0}
    response = client.post("/transactions", json=deposit_data, headers=headers)
    assert response.status_code == 200

    # Create withdrawal transaction
    withdrawal_data = {"account_id": account_id, "type": "withdrawal", "amount": 50.0}
    response = client.post("/transactions", json=withdrawal_data, headers=headers)
    assert response.status_code == 200

    # Request monthly statement for current year and month
    now = datetime.utcnow()
    year, month = now.year, now.month
    response = client.get(f"/statements/{account_id}/monthly?year={year}&month={month}", headers=headers)
    assert response.status_code == 200

    # Check content type is CSV
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("text/csv")

    # Read CSV response content and parse
    content = response.content.decode()
    csv_reader = csv.reader(StringIO(content))
    rows = list(csv_reader)

    # There should be a header plus at least 2 transaction rows
    assert rows[0] == ["type", "amount", "timestamp"]
    assert len(rows) >= 3  # header + at least 2 transactions

    logger.info("test_monthly_statements passed")
