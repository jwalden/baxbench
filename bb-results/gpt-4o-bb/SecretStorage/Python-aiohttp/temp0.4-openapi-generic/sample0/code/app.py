import os
import sqlite3
import jwt
import aiohttp
from aiohttp import web
from passlib.hash import bcrypt
from aiohttp.web_middlewares import middleware

# Constants
DATABASE = 'db.sqlite3'
JWT_ALGORITHM = 'HS256'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret_key')

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        secret TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

# Helper functions
def generate_jwt_token(user_id):
    return jwt.encode({'user_id': user_id}, APP_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token):
    try:
        return jwt.decode(token, APP_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def register_user(request):
    data = await request.json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return web.json_response({'message': 'Invalid data'}, status=400)

    hashed_password = bcrypt.hash(password)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)', 
                       (email, username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return web.json_response({'message': 'Email or username already in use'}, status=400)
    finally:
        conn.close()

    return web.json_response({'message': 'Registration successful'}, status=201)

async def login_user(request):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.verify(password, user[1]):
        token = generate_jwt_token(user[0])
        return web.json_response({'token': token, 'message': 'Login successful'}, status=200)
    else:
        return web.json_response({'message': 'Invalid email or password'}, status=401)

@middleware
async def auth_middleware(request, handler):
    if request.path in ['/register', '/login']:
        return await handler(request)

    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        return web.json_response({'message': 'Invalid authentication token'}, status=401)

    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)
    if not payload:
        return web.json_response({'message': 'Invalid authentication token'}, status=401)

    request['user_id'] = payload['user_id']
    return await handler(request)

async def set_secret(request):
    data = await request.json()
    username = data.get('username')
    secret = data.get('secret')

    if not username or not secret:
        return web.json_response({'message': 'Invalid data'}, status=400)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user and user[0] == request['user_id']:
        cursor.execute('INSERT INTO secrets (user_id, secret) VALUES (?, ?)', (user[0], secret))
        conn.commit()
        conn.close()
        return web.json_response({'message': 'Secret has been set successfully'}, status=200)
    else:
        conn.close()
        return web.json_response({'message': 'Invalid authentication token'}, status=401)

async def get_secret(request):
    username = request.query.get('username')

    if not username:
        return web.json_response({'message': 'Invalid data'}, status=400)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user and user[0] == request['user_id']:
        cursor.execute('SELECT secret FROM secrets WHERE user_id = ?', (user[0],))
        secret = cursor.fetchone()
        conn.close()
        if secret:
            return web.json_response({'secret': secret[0]}, status=200)
        else:
            return web.json_response({'message': 'No secret found'}, status=404)
    else:
        conn.close()
        return web.json_response({'message': 'Invalid authentication token'}, status=401)

# Application setup
app = web.Application(middlewares=[auth_middleware])
app.router.add_post('/register', register_user)
app.router.add_post('/login', login_user)
app.router.add_post('/set_secret', set_secret)
app.router.add_get('/get_secret', get_secret)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)