import os
import sqlite3
import jwt
import hashlib
from aiohttp import web
from passlib.hash import bcrypt
from functools import wraps

APP_SECRET = os.getenv("APP_SECRET", "your-default-secret")

# Initialize the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            secret TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Utility function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

# JWT Token generation
def generate_token(user_id):
    payload = {'user_id': user_id}
    return jwt.encode(payload, APP_SECRET, algorithm='HS256')

# JWT Token verification
def verify_token(token):
    try:
        payload = jwt.decode(token, APP_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Decorator for protected routes
def login_required(f):
    @wraps(f)
    async def decorated_function(request, *args, **kwargs):
        token = request.headers.get('Authorization', None)
        if token is None or not token.startswith("Bearer "):
            return web.json_response({'message': 'Invalid authentication token'}, status=401)
        
        token = token.split(" ")[1]
        user_id = verify_token(token)
        if user_id is None:
            return web.json_response({'message': 'Invalid authentication token'}, status=401)
        
        request['user_id'] = user_id
        return await f(request, *args, **kwargs)
    return decorated_function

# User registration
async def register(request):
    data = await request.json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return web.json_response({'message': 'Invalid data'}, status=400)

    hashed_password = bcrypt.hash(password)
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)', (email, username, hashed_password))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return web.json_response({'message': 'Email or username already in use'}, status=400)

    return web.json_response({'message': 'Registration successful'}, status=201)

# User login
async def login(request):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return web.json_response({'message': 'Invalid email or password'}, status=401)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, password FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()

    if user is None or not bcrypt.verify(password, user['password']):
        return web.json_response({'message': 'Invalid email or password'}, status=401)

    token = generate_token(user['id'])
    return web.json_response({'token': token, 'message': 'Login successful'}, status=200)

# Set secret
@login_required
async def set_secret(request):
    data = await request.json()
    username = data.get('username')
    secret = data.get('secret')

    if not username or not secret:
        return web.json_response({'message': 'Invalid data'}, status=400)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = c.fetchone()

    if user is None or user['id'] != request['user_id']:
        conn.close()
        return web.json_response({'message': 'Invalid authentication token'}, status=401)

    c.execute('INSERT INTO secrets (user_id, secret) VALUES (?, ?)', (user['id'], secret))
    conn.commit()
    conn.close()

    return web.json_response({'message': 'Secret has been set successfully'}, status=200)

# Get secret
@login_required
async def get_secret(request):
    username = request.query.get('username')

    if not username:
        return web.json_response({'message': 'Invalid data'}, status=400)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = c.fetchone()

    if user is None or user['id'] != request['user_id']:
        conn.close()
        return web.json_response({'message': 'Invalid authentication token'}, status=401)

    c.execute('SELECT secret FROM secrets WHERE user_id = ?', (user['id'],))
    secret = c.fetchone()
    conn.close()

    if secret is None:
        return web.json_response({'message': 'No secret found'}, status=404)

    return web.json_response({'secret': secret['secret']}, status=200)

# Initialize the web application
def create_app():
    app = web.Application()
    app.router.add_post('/register', register)
    app.router.add_post('/login', login)
    app.router.add_post('/set_secret', set_secret)
    app.router.add_get('/get_secret', get_secret)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)