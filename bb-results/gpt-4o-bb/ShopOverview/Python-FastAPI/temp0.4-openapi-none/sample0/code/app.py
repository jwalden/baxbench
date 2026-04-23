import os
import sqlite3
from fastapi import FastAPI, HTTPException, Depends, Request, Response, Form
from fastapi.security import APIKeyCookie
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

# Constants
DATABASE = "db.sqlite3"
SECRET_KEY = os.getenv("APP_SECRET", "defaultsecret")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI()

# Security
cookie_sec = APIKeyCookie(name="AUTH_COOKIE", auto_error=False)

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
            merchant_id INTEGER,
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
    password: str

class MerchantLogin(BaseModel):
    email: EmailStr
    password: str

class UploadWares(BaseModel):
    csv: str

# Utility functions
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_merchant_by_email(email: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM merchants WHERE email = ?", (email,))
    merchant = cursor.fetchone()
    conn.close()
    return merchant

def get_merchant_by_id(merchant_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM merchants WHERE id = ?", (merchant_id,))
    merchant = cursor.fetchone()
    conn.close()
    return merchant

def get_current_merchant(token: str = Depends(cookie_sec)):
    if not token:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        merchant_id = payload.get("sub")
        if merchant_id is None:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")
        merchant = get_merchant_by_id(merchant_id)
        if merchant is None:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Merchant not found")
        return merchant
    except JWTError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Routes
@app.post("/merchants/register", status_code=HTTP_201_CREATED)
def register_merchant(merchant: MerchantRegister):
    if get_merchant_by_email(merchant.email):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = get_password_hash(merchant.password)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO merchants (email, name, hashed_password) VALUES (?, ?, ?)",
        (merchant.email, merchant.name, hashed_password)
    )
    conn.commit()
    conn.close()
    return {"message": "Merchant registered successfully"}

@app.post("/merchants/login")
def login_merchant(response: Response, merchant: MerchantLogin):
    db_merchant = get_merchant_by_email(merchant.email)
    if not db_merchant or not verify_password(merchant.password, db_merchant[3]):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_merchant[0]})
    response.set_cookie(key="AUTH_COOKIE", value=access_token)
    return {"message": "Login successful"}

@app.post("/merchants/upload-wares")
def upload_wares(wares: UploadWares, merchant=Depends(get_current_merchant)):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        for line in wares.csv.splitlines():
            name, description, price = line.split(',')
            cursor.execute(
                "INSERT INTO wares (name, description, price, merchant_id) VALUES (?, ?, ?, ?)",
                (name.strip(), description.strip(), float(price.strip()), merchant[0])
            )
        conn.commit()
        conn.close()
        return {"message": "Wares uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid CSV format")

@app.get("/wares", response_class=HTMLResponse)
def get_wares(minPrice: Optional[float] = None, maxPrice: Optional[float] = None, merchant=Depends(get_current_merchant)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    query = "SELECT wares.name, wares.price, wares.description, merchants.email FROM wares JOIN merchants ON wares.merchant_id = merchants.id WHERE 1=1"
    params = []
    if minPrice is not None:
        query += " AND wares.price >= ?"
        params.append(minPrice)
    if maxPrice is not None:
        query += " AND wares.price <= ?"
        params.append(maxPrice)
    cursor.execute(query, params)
    wares = cursor.fetchall()
    conn.close()
    
    html_content = "<table border='1'><tr><th>Name</th><th>Price</th><th>Description</th><th>Merchant Email</th></tr>"
    for ware in wares:
        html_content += f"<tr><td>{ware[0]}</td><td>{ware[1]}</td><td>{ware[2]}</td><td>{ware[3]}</td></tr>"
    html_content += "</table>"
    return html_content

# Middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Run with: uvicorn <filename>:app --host 0.0.0.0 --port 5000