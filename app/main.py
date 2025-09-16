from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
from app.database import get_db, init_db
from app.auth import authenticate_user, create_access_token, get_current_user
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import hashlib

from app.cards import router as cards_router
from app.money_transfer import router as money_transfer_router


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
app.include_router(cards_router)
app.include_router(money_transfer_router)



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
