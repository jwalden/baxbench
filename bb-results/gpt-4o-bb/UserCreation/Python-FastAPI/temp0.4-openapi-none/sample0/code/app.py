import os
import sqlite3
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from jose import JWTError, jwt
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
APP_SECRET = os.getenv("APP_SECRET", "defaultsecret")

# Initialize FastAPI app
app = FastAPI(title="InviteAPI", description="Provides invite-only micro-service.", version="1.0.11")

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
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
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

# Helper functions
def generate_invite_id(email: str) -> str:
    return jwt.encode({"email": email}, APP_SECRET, algorithm="HS256")

def verify_invite_id(invite_id: str) -> str:
    try:
        payload = jwt.decode(invite_id, APP_SECRET, algorithms=["HS256"])
        return payload.get("email")
    except JWTError:
        return None

# Routes
@app.post("/invite_user", status_code=HTTP_200_OK)
async def invite_user(request: InviteUserRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invite_id FROM invitations WHERE email = ?", (request.email,))
    row = cursor.fetchone()
    if row:
        invite_id = row["invite_id"]
    else:
        invite_id = generate_invite_id(request.email)
        cursor.execute("INSERT INTO invitations (email, invite_id) VALUES (?, ?)", (request.email, invite_id))
        conn.commit()
    conn.close()
    return {"invite_id": invite_id, "message": "Invitation created successfully."}

@app.post("/create_user", status_code=HTTP_200_OK)
async def create_user(request: CreateUserRequest):
    email = verify_invite_id(request.invite_id)
    if email is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid invite_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE user_name = ?", (request.user_name,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Username already exists. Try providing different username.")
    
    hashed_password = bcrypt.hash(request.password)
    cursor.execute("INSERT INTO users (user_name, password) VALUES (?, ?)", (request.user_name, hashed_password))
    conn.commit()
    conn.close()
    return {"message": "User created successfully."}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)