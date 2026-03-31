import os
import sqlite3
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.status import HTTP_401_UNAUTHORIZED
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
APP_SECRET = os.getenv("APP_SECRET", "your-secret-key")

# Initialize FastAPI app
app = FastAPI(title="InviteAPI", description="Provides invite-only micro-service.", version="1.0.11")

# Initialize security and hashing utilities
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
DATABASE = "db.sqlite3"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        invite_id TEXT UNIQUE NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models
class InviteUserRequest(BaseModel):
    email: EmailStr

class CreateUserRequest(BaseModel):
    invite_id: str
    user_name: str
    password: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_invite_token(email: str):
    return jwt.encode({"email": email}, APP_SECRET, algorithm="HS256")

def decode_invite_token(token: str):
    try:
        payload = jwt.decode(token, APP_SECRET, algorithms=["HS256"])
        return payload.get("email")
    except JWTError:
        return None

# Endpoints
@app.post("/invite_user", response_model=dict)
async def invite_user(request: InviteUserRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invite_id FROM invitations WHERE email = ?", (request.email,))
    row = cursor.fetchone()
    if row:
        invite_id = row["invite_id"]
    else:
        invite_id = create_invite_token(request.email)
        cursor.execute("INSERT INTO invitations (email, invite_id) VALUES (?, ?)", (request.email, invite_id))
        conn.commit()
    conn.close()
    return {"invite_id": invite_id, "message": "Invitation created successfully."}

@app.post("/create_user", response_model=dict)
async def create_user(request: CreateUserRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM invitations WHERE invite_id = ?", (request.invite_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid invite_id")
    
    cursor.execute("SELECT user_name FROM users WHERE user_name = ?", (request.user_name,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists. Try providing different username.")
    
    hashed_password = get_password_hash(request.password)
    cursor.execute("INSERT INTO users (user_name, password) VALUES (?, ?)", (request.user_name, hashed_password))
    conn.commit()
    conn.close()
    return {"message": "User created successfully."}

# To run the app, use: uvicorn <filename>:app --host 0.0.0.0 --port 5000