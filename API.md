# Banking API Backend

A FastAPI-based banking application backend that provides comprehensive financial services including user authentication, account management, transactions, money transfers, and card management.

## Features

- **User Management**: Registration and JWT-based authentication
- **Account Operations**: Create and manage multiple bank accounts
- **Transactions**: Deposit, withdrawal, and transfer capabilities
- **External Transfers**: Send money to external accounts with limits
- **Card Management**: Create, manage, and control debit/credit cards
- **Statement Generation**: Export monthly transaction statements as CSV
- **Secure Authentication**: JWT tokens with account ownership verification

## Project Structure

```
app/
├── main.py              # Main FastAPI application and core endpoints
├── database.py          # Database connection and initialization
├── auth.py              # Authentication and JWT handling
├── cards.py             # Card management endpoints
├── statements.py        # Statement generation endpoints
├── money_transfer.py    # External transfer functionality
└── bank.db              # SQLite database (created automatically)
requirements.txt
```

## Prerequisites

- Python 3.8+
- pip (Python package installer)

## Installation & Setup

1. **Clone or download the project files**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv banking_env
   source banking_env/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```bash
   python -c "from app.database import init_db; init_db()"
   ```

5. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the application**:
   - API: http://127.0.0.1:8000

## API Documentation

### Authentication

#### Register User
```http
POST /signup
Content-Type: application/json

{
  "username": "npatel",
  "password": "12345678patel",
  "full_name": "Nishchay Patel"
}
```

#### Login
```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=npatel&password=12345678patel
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Account Management

#### Create Account
```http
POST /accounts
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "initial_balance": 1000.0
}
```

#### List Accounts
```http
GET /accounts
Authorization: Bearer <your_token>
```

Response:
```json
{
  "accounts": [
    {
      "id": 1,
      "balance": 1000.0
    }
  ]
}
```

### Transactions

#### Create Transaction (Deposit/Withdrawal)
```http
POST /transactions
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "account_id": 1,
  "type": "deposit",
  "amount": 500.0
}
```

#### Internal Transfer
```http
POST /transfers
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "from_account_id": 1,
  "to_account_id": 2,
  "amount": 250.0
}
```

#### External Transfer
```http
POST /external-transfer
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "from_account_id": 1,
  "external_account": "Chase123456789",
  "amount": 1000.0
}
```

### Card Management

#### Create Card
```http
POST /cards
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "account_id": 1,
  "card_type": "debit",
  "expiry": "12/25"
}
```

#### Update Card Status
```http
PUT /cards/{card_id}/status
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "status": "blocked"
}
```

#### Update Card PIN
```http
PUT /cards/{card_id}/pin
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "pin": "1234"
}
```

#### Delete Card
```http
DELETE /cards/{card_id}
Authorization: Bearer <your_token>
```

### Statements

#### Get Transaction History
```http
GET /statements/{account_id}
Authorization: Bearer <your_token>
```

#### Export Monthly Statement (CSV)
```http
GET /statements/{account_id}/monthly?year=2025&month=9
Authorization: Bearer <your_token>
```

This endpoint returns a CSV file download with the format:
```csv
type,amount,timestamp
deposit,500.0,2025-09-15 14:30:00
withdrawal,100.0,2025-09-15 15:45:00
```

## Database Schema

### Users Table
- `id`: Primary key (auto-increment)
- `username`: Unique username
- `hashed_password`: SHA256 hashed password
- `full_name`: User's full name

### Accounts Table
- `id`: Primary key (auto-increment)
- `user_id`: Foreign key to users table
- `balance`: Account balance (decimal)

### Transactions Table
- `id`: Primary key (auto-increment)
- `account_id`: Foreign key to accounts table
- `type`: Transaction type ('deposit', 'withdrawal', 'transfer', 'external_transfer')
- `amount`: Transaction amount (positive for deposits, negative for withdrawals/transfers)
- `timestamp`: Transaction timestamp (auto-generated)

### Cards Table
- `id`: Primary key (auto-increment)
- `account_id`: Foreign key to accounts table
- `card_number`: 16-digit card number (unique)
- `card_type`: Card type ('debit' or 'credit')
- `expiry`: Card expiry date (MM/YY format)
- `status`: Card status ('active' or 'blocked')
- `pin`: Card PIN (stored as plain text - for demo only)

## Authentication

All endpoints except `/signup` and `/token` require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Tokens expire after 30 minutes and need to be refreshed by logging in again.

## Development

### Running Tests
Refer the Test README.md

### Configuration
Key configuration values are hardcoded in the application:
- Secret key for JWT signing (change in production)
- Token expiration time (30 minutes)
- External transfer limit ($5,000)

### Database Management
The SQLite database is created automatically on first run. For production, might use cloud.

## Production Considerations

1. Use a secure secret key for JWT signing
2. Implement better password hashing (bcrypt/Argon2)
3. More robust pydantic validation.
4. May need proper logging and monitoring
5. Use a production database (PostgreSQL/MySQL)
6. Implement comprehensive error handling
7. Use environment variables for configuration
8. Implement proper security headers and HTTPS