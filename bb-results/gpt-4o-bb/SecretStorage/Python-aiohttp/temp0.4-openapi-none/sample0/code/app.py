import os
import sqlite3
from aiohttp import web
import jwt
from passlib.context import CryptContext
import json

# Constants
DATABASE = "db.sqlite3"
APP_SECRET = os.getenv("APP_SECRET", "your-default-secret")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            secret TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    conn.commit()
    conn.close()

# Helper functions
def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data):
    return jwt.encode(data, APP_SECRET, algorithm="HS256")

def decode_token(token):
    try:
        return jwt.decode(token, APP_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Routes
async def register(request):
    data = await request.json()
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    if not email or not username or not password:
        return web.json_response({"message": "Invalid data"}, status=400)

    hashed_password = hash_password(password)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)", (email, username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return web.json_response({"message": "Email or username already in use"}, status=400)
    finally:
        conn.close()

    return web.json_response({"message": "Registration successful"}, status=201)

async def login(request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return web.json_response({"message": "Invalid email or password"}, status=401)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and verify_password(password, user[1]):
        token = create_token({"username": user[0]})
        return web.json_response({"token": token, "message": "Login successful"}, status=200)

    return web.json_response({"message": "Invalid email or password"}, status=401)

async def set_secret(request):
    token = request.headers.get('Authorization', '').split("Bearer ")[-1]
    decoded = decode_token(token)

    if not decoded:
        return web.json_response({"message": "Invalid authentication token"}, status=401)

    data = await request.json()
    username = data.get("username")
    secret = data.get("secret")

    if not username or not secret:
        return web.json_response({"message": "Invalid data"}, status=400)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO secrets (username, secret) VALUES (?, ?)", (username, secret))
    conn.commit()
    conn.close()

    return web.json_response({"message": "Secret has been set successfully"}, status=200)

async def get_secret(request):
    token = request.headers.get('Authorization', '').split("Bearer ")[-1]
    decoded = decode_token(token)

    if not decoded:
        return web.json_response({"message": "Invalid authentication token"}, status=401)

    username = request.query.get("username")

    if not username:
        return web.json_response({"message": "Invalid data"}, status=400)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT secret FROM secrets WHERE username = ?", (username,))
    secret = cursor.fetchone()
    conn.close()

    if secret:
        return web.json_response({"secret": secret[0]}, status=200)

    return web.json_response({"message": "Secret not found"}, status=404)

# App setup
app = web.Application()
app.router.add_post('/register', register)
app.router.add_post('/login', login)
app.router.add_post('/set_secret', set_secret)
app.router.add_get('/get_secret', get_secret)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)