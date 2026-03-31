import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, Depends, status, Form
from fastapi.security import APIKeyCookie
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr, constr
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from fastapi.encoders import jsonable_encoder

# Constants
DATABASE = "db.sqlite3"
SECRET_KEY = os.getenv("APP_SECRET", "default_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app
app = FastAPI()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cookie-based authentication
cookie_auth = APIKeyCookie(name="AUTH_COOKIE")

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            hashed_password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            merchant_id INTEGER NOT NULL,
            FOREIGN KEY (merchant_id) REFERENCES merchants (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models
class MerchantRegister(BaseModel):
    email: EmailStr
    name: str
    password: constr(min_length=8)

class MerchantLogin(BaseModel):
    email: EmailStr
    password: str

class WaresUpload(BaseModel):
    csv: str

# Utility functions
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def get_current_merchant(token: str = Depends(cookie_auth)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return payload

# Routes
@app.post("/merchants/register", status_code=status.HTTP_201_CREATED)
def register_merchant(merchant: MerchantRegister):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO merchants (email, name, hashed_password) VALUES (?, ?, ?)",
            (merchant.email, merchant.name, get_password_hash(merchant.password))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    finally:
        conn.close()
    return {"message": "Merchant registered successfully"}

@app.post("/merchants/login", response_class=JSONResponse)
def login_merchant(merchant: MerchantLogin, response: JSONResponse):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, hashed_password FROM merchants WHERE email = ?", (merchant.email,))
    result = cursor.fetchone()
    conn.close()
    if not result or not verify_password(merchant.password, result[1]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token({"sub": merchant.email})
    response.set_cookie(key="AUTH_COOKIE", value=token, httponly=True)
    return {"message": "Login successful"}

@app.post("/merchants/upload-wares", dependencies=[Depends(get_current_merchant)])
def upload_wares(wares: WaresUpload, current_merchant: dict = Depends(get_current_merchant)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    merchant_email = current_merchant["sub"]
    cursor.execute("SELECT id FROM merchants WHERE email = ?", (merchant_email,))
    merchant_id = cursor.fetchone()[0]
    
    try:
        for line in wares.csv.strip().split("\n"):
            name, description, price = line.split(",")
            cursor.execute(
                "INSERT INTO wares (name, description, price, merchant_id) VALUES (?, ?, ?, ?)",
                (name.strip(), description.strip(), float(price.strip()), merchant_id)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV format")
    finally:
        conn.close()
    return {"message": "Wares uploaded successfully"}

@app.get("/wares", response_class=HTMLResponse, dependencies=[Depends(get_current_merchant)])
def get_wares(minPrice: Optional[float] = None, maxPrice: Optional[float] = None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    query = "SELECT wares.name, wares.description, wares.price, merchants.email FROM wares JOIN merchants ON wares.merchant_id = merchants.id WHERE 1=1"
    params = []
    if minPrice is not None:
        query += " AND wares.price >= ?"
        params.append(minPrice)
    if maxPrice is not None:
        query += " AND wares.price <= ?"
        params.append(maxPrice)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    html_content = "<table><tr><th>Name</th><th>Description</th><th>Price</th><th>Merchant Email</th></tr>"
    for row in rows:
        html_content += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
    html_content += "</table>"
    return HTMLResponse(content=html_content)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)