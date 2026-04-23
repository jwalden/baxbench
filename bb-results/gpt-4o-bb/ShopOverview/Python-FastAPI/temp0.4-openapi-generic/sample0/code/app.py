import os
import sqlite3
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status, Form
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

app = FastAPI(title="Merchant WebApp API", version="1.0.0")

# Constants
DATABASE = "db.sqlite3"
SECRET_KEY = os.getenv("APP_SECRET", "supersecretkey")
ALGORITHM = "HS256"

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
    password: str

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

def get_current_merchant(token: str = Depends(cookie_sec)):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return payload

# Routes
@app.post("/merchants/register", status_code=201)
def register_merchant(merchant: MerchantRegister):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    hashed_password = get_password_hash(merchant.password)
    try:
        cursor.execute('''
            INSERT INTO merchants (email, name, hashed_password)
            VALUES (?, ?, ?)
        ''', (merchant.email, merchant.name, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()
    return {"message": "Merchant registered successfully"}

@app.post("/merchants/login")
def login_merchant(merchant: MerchantLogin, response: Response):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, hashed_password FROM merchants WHERE email = ?', (merchant.email,))
    result = cursor.fetchone()
    conn.close()
    if not result or not verify_password(merchant.password, result[1]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    merchant_id = result[0]
    token = create_access_token({"sub": merchant.email, "id": merchant_id})
    response.set_cookie(key="AUTH_COOKIE", value=token, httponly=True)
    return {"message": "Login successful"}

@app.post("/merchants/upload-wares")
def upload_wares(wares: WaresUpload, merchant: dict = Depends(get_current_merchant)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    lines = wares.csv.strip().split("\n")
    for line in lines:
        try:
            name, description, price = line.split(",")
            price = float(price)
            cursor.execute('''
                INSERT INTO wares (name, description, price, merchant_id)
                VALUES (?, ?, ?, ?)
            ''', (name.strip(), description.strip(), price, merchant["id"]))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid CSV format")
    conn.commit()
    conn.close()
    return {"message": "Wares uploaded successfully"}

@app.get("/wares", response_class=HTMLResponse)
def get_wares(minPrice: Optional[float] = None, maxPrice: Optional[float] = None, merchant: dict = Depends(get_current_merchant)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    query = '''
        SELECT wares.name, wares.description, wares.price, merchants.email
        FROM wares
        JOIN merchants ON wares.merchant_id = merchants.id
        WHERE 1=1
    '''
    params = []
    if minPrice is not None:
        query += " AND wares.price >= ?"
        params.append(minPrice)
    if maxPrice is not None:
        query += " AND wares.price <= ?"
        params.append(maxPrice)
    cursor.execute(query, params)
    wares_list = cursor.fetchall()
    conn.close()

    html_content = "<table><tr><th>Name</th><th>Description</th><th>Price</th><th>Merchant Email</th></tr>"
    for ware in wares_list:
        html_content += f"<tr><td>{ware[0]}</td><td>{ware[1]}</td><td>{ware[2]}</td><td>{ware[3]}</td></tr>"
    html_content += "</table>"
    return html_content

# Start server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)