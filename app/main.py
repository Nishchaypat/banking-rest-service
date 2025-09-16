from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
from app.database import get_db, init_db
from app.auth import authenticate_user, create_access_token, get_current_user
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import hashlib

from app.cards import router as cards_router


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
app.include_router(cards_router)


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
