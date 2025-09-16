from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
from app.database import get_db, init_db
from app.auth import authenticate_user, create_access_token, get_current_user
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import hashlib

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# User schema for registration
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None


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