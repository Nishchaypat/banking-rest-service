from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
from app.database import get_db, init_db
from app.auth import authenticate_user, create_access_token, get_current_user
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import hashlib
import random
from datetime import datetime, timedelta

from app.cards import router as cards_router
from app.money_transfer import router as money_transfer_router
from app.statements import router as statements_router

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
app.include_router(cards_router)
app.include_router(money_transfer_router)
app.include_router(statements_router)




# User schema for registration
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None

class CardCreate(BaseModel):
    account_id: int
    card_type: str  # 'debit' or 'credit'
    expiry: str  # 'MM/YY'

class AccountCreate(BaseModel):
    initial_balance: float = 0.0

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float

class TransactionCreate(BaseModel):
    account_id: int
    type: str  # 'deposit' or 'withdrawal'
    amount: float

@app.on_event("startup")
def startup():
    init_db()

# Register new user endpoint
@app.post("/signup")
def register_user(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()
    hashed_pw = hashlib.sha256(user.password.encode()).hexdigest()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password, full_name) VALUES (?, ?, ?)",
            (user.username, hashed_pw, user.full_name)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()
    return {"message": "User created successfully"}

# Login endpoint to get JWT token
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    user = authenticate_user(conn, form_data.username, form_data.password)
    conn.close()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/accounts")
def create_account(account: AccountCreate, username: str = Security(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor.execute(
        "INSERT INTO accounts (user_id, balance) VALUES (?, ?)",
        (user["id"], account.initial_balance)
    )
    conn.commit()
    conn.close()
    return {"message": "Account created successfully"}

@app.get("/accounts")
def list_accounts(username: str = Security(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor.execute("SELECT id, balance FROM accounts WHERE user_id = ?", (user["id"],))
    accounts = cursor.fetchall()
    conn.close()
    return {"accounts": [{"id": acc["id"], "balance": acc["balance"]} for acc in accounts]}

def generate_card_number() -> str:
    # Generate a simple random 16-digit card number (unsafe for real use)
    return ''.join(str(random.randint(0, 9)) for _ in range(16))


@app.post("/cards")
def create_card(card: CardCreate, username: str = Security(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    # Verify ownership of account
    cursor.execute(
        "SELECT a.id FROM accounts a JOIN users u ON a.user_id = u.id WHERE a.id = ? AND u.username = ?",
        (card.account_id, username)
    )
    account = cursor.fetchone()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    card_number = generate_card_number()
    try:
        cursor.execute(
            "INSERT INTO cards (account_id, card_number, card_type, expiry) VALUES (?, ?, ?, ?)",
            (card.account_id, card_number, card.card_type, card.expiry)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Card number generation conflict, try again")
    finally:
        conn.close()
    return {"message": "Card created successfully", "card_number": card_number}

@app.post("/transfers")
def transfer_money(transfer: TransferCreate, username: str = Security(get_current_user)):
    if transfer.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if transfer.from_account_id == transfer.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")
    conn = get_db()
    cursor = conn.cursor()
    # Verify ownership of source account
    cursor.execute(
        "SELECT balance FROM accounts a JOIN users u ON a.user_id = u.id WHERE a.id = ? AND u.username = ?",
        (transfer.from_account_id, username)
    )
    from_acc = cursor.fetchone()
    if not from_acc:
        conn.close()
        raise HTTPException(status_code=404, detail="Source account not found or unauthorized")
    if from_acc["balance"] < transfer.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds in source account")
    # Verify target account exists
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (transfer.to_account_id,))
    to_acc = cursor.fetchone()
    if not to_acc:
        conn.close()
        raise HTTPException(status_code=404, detail="Target account not found")
    # Perform transfer within a transaction
    new_from_balance = from_acc["balance"] - transfer.amount
    new_to_balance = to_acc["balance"] + transfer.amount
    try:
        cursor.execute("BEGIN")
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_from_balance, transfer.from_account_id))
        cursor.execute("INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
                       (transfer.from_account_id, "transfer", -transfer.amount))
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_to_balance, transfer.to_account_id))
        cursor.execute("INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
                       (transfer.to_account_id, "transfer", transfer.amount))
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Transfer failed due to server error")
    finally:
        conn.close()
    return {"message": "Transfer successful"}

@app.get("/statements/{account_id}")
def get_statements(account_id: int, username: str = Security(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    # Confirm account ownership
    cursor.execute(
        "SELECT a.id FROM accounts a JOIN users u ON a.user_id = u.id WHERE a.id = ? AND u.username = ?",
        (account_id, username)
    )
    account = cursor.fetchone()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")
    # Fetch transaction statements
    cursor.execute(
        "SELECT type, amount, timestamp FROM transactions WHERE account_id = ? ORDER BY timestamp DESC",
        (account_id,)
    )
    transactions = cursor.fetchall()
    conn.close()
    return {"statements": [{"type": t["type"], "amount": t["amount"], "timestamp": t["timestamp"]} for t in transactions]}

@app.post("/transactions")
def create_transaction(transaction: TransactionCreate, username: str = Security(get_current_user)):
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Verify account ownership (fully qualify column)
        cursor.execute(
            "SELECT a.balance FROM accounts a "
            "JOIN users u ON a.user_id = u.id "
            "WHERE a.id = ? AND u.username = ?",
            (transaction.account_id, username)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found or unauthorized")
        current_balance = row["balance"]
        new_balance = current_balance
        if transaction.type == "deposit":
            new_balance += transaction.amount
        elif transaction.type == "withdrawal":
            if current_balance < transaction.amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            new_balance -= transaction.amount
        else:
            raise HTTPException(status_code=400, detail="Invalid transaction type")
        # Update balance and insert transaction
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, transaction.account_id))
        cursor.execute(
            "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
            (transaction.account_id, transaction.type, transaction.amount)
        )
        conn.commit()
        return {"message": f"{transaction.type.capitalize()} successful", "new_balance": new_balance}
    finally:
        conn.close()

@app.get("/accounts/{account_id}/transactions")
def list_transactions(account_id: int, username: str = Security(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Verify account belongs to the user (fully qualify columns)
        cursor.execute(
            "SELECT a.id FROM accounts a "
            "JOIN users u ON a.user_id = u.id "
            "WHERE a.id = ? AND u.username = ?",
            (account_id, username)
        )
        account = cursor.fetchone()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found or unauthorized")
        # Fetch transactions for that account (fully qualify all columns)
        cursor.execute(
            "SELECT transactions.id, transactions.type, transactions.amount, transactions.timestamp "
            "FROM transactions WHERE transactions.account_id = ? "
            "ORDER BY transactions.timestamp DESC",
            (account_id,)
        )
        txns = cursor.fetchall()
        return {
            "transactions": [
                {"id": t["id"], "type": t["type"], "amount": t["amount"], "timestamp": t["timestamp"]}
                for t in txns
            ]
        }
    finally:
        conn.close()