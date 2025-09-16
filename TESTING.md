# Testing Guide for Banking API

This guide explains how to set up and run the automated tests for the Banking API. We use pytest and FastAPI's TestClient, and tests run against a separate test database.

## Prerequisites

- Python 3.8+
- pytest
- requests (for stress/demo client)

## Test Database Configuration

By default, the application uses `bank.db`. To avoid interfering with production data when testing, point the app to a separate test database:

```bash
export DATABASE_PATH="./tests/test_bank.db"
```

This environment variable must be set before starting the API server or running tests.

## Start the API Server

Run the FastAPI app on port 8001 with the test database:

```bash
uvicorn app.main:app --reload --port 8001
```

Ensure the DATABASE_PATH env var is exported in the same shell.

## Running Unit and Integration Tests

All pytest tests are located under the tests/ directory. To execute them:

```bash
pytest
```

This will:
- Create tables in tests/test_bank.db via init_db() on startup
- Use fixtures in conftest.py (`client`, signup_user, login_user)
- Run tests for auth, accounts, transactions, transfers, cards, and statements

## Running the Demo Test Client

The demo client (`user_flow.py`) exercises the full API flow. To run it:

```bash
python3 user_flow.py
```


Both modes will operate against http://127.0.0.1:8001 by default.

## Clean Up

After tests complete, you can remove the test database:

```bash
rm ./tests/test_bank.db
```

## Notes

- user_flow.py requires the server to be running on port 8001.