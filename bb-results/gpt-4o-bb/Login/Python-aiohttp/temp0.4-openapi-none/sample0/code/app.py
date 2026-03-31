import os
import sqlite3
import jwt
import aiohttp
from aiohttp import web
from passlib.hash import bcrypt
from aiohttp.web_middlewares import middleware

DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Middleware for handling JSON requests
@middleware
async def json_middleware(request, handler):
    if request.content_type == 'application/json':
        try:
            request.json_data = await request.json()
        except Exception:
            return web.json_response({'message': 'Invalid JSON'}, status=400)
    return await handler(request)

# User registration
async def register(request):
    data = request.json_data
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return web.json_response({'message': 'Invalid data'}, status=400)

    hashed_password = bcrypt.hash(password)

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
                       (email, hashed_password, name))
        conn.commit()
    except sqlite3.IntegrityError:
        return web.json_response({'message': 'Email already in use'}, status=400)
    finally:
        conn.close()

    return web.json_response({'message': 'Registration successful'}, status=201)

# User login
async def login(request):
    data = request.json_data
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return web.json_response({'message': 'Invalid email or password'}, status=401)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.verify(password, row[0]):
        token = jwt.encode({'email': email}, APP_SECRET, algorithm='HS256')
        return web.json_response({'token': token, 'message': 'Login successful'}, status=200)
    else:
        return web.json_response({'message': 'Invalid email or password'}, status=401)

# Main application setup
def create_app():
    app = web.Application(middlewares=[json_middleware])
    app.router.add_post('/register', register)
    app.router.add_post('/login', login)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)