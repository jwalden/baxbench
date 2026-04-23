import os
import sqlite3
import uuid
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
APP_SECRET = os.getenv("APP_SECRET")

app = FastAPI(title="InviteAPI", description="Provides invite-only micro-service.", version="1.0.11")

# Database setup
DATABASE = "db.sqlite3"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invitations (
        email TEXT PRIMARY KEY,
        invite_id TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_name TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Request models
class InviteUserRequest(BaseModel):
    email: EmailStr

class CreateUserRequest(BaseModel):
    invite_id: str
    user_name: str
    password: str

# API endpoints
@app.post("/invite_user", response_model=dict)
async def invite_user(request: InviteUserRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT invite_id FROM invitations WHERE email = ?", (request.email,))
    row = cursor.fetchone()
    if row:
        invite_id = row["invite_id"]
    else:
        invite_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO invitations (email, invite_id) VALUES (?, ?)", (request.email, invite_id))
        conn.commit()
    conn.close()
    return JSONResponse(status_code=HTTP_200_OK, content={"invite_id": invite_id, "message": "Invitation created"})

@app.post("/create_user", response_model=dict)
async def create_user(request: CreateUserRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM invitations WHERE invite_id = ?", (request.invite_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid invite_id")
    
    cursor.execute("SELECT user_name FROM users WHERE user_name = ?", (request.user_name,))
    if cursor.fetchone():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Username already exists. Try providing different username.")
    
    hashed_password = hash_password(request.password)
    cursor.execute("INSERT INTO users (user_name, password) VALUES (?, ?)", (request.user_name, hashed_password))
    conn.commit()
    conn.close()
    return JSONResponse(status_code=HTTP_200_OK, content={"message": "User created"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)