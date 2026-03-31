import os
import sqlite3
import jwt
import json
from aiohttp import web
from passlib.hash import bcrypt
from aiohttp.web_middlewares import middleware

# Constants
DATABASE = 'db.sqlite3'
JWT_SECRET = os.environ.get('APP_SECRET', 'defaultsecret')
JWT_ALGORITHM = 'HS256'

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

# Helper functions
def generate_jwt(email):
    return jwt.encode({'email': email}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded['email']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Routes
async def login(request):
    try:
        data = await request.json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return web.json_response({'message': 'Invalid email or password'}, status=401)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        conn.close()

        if result and bcrypt.verify(password, result[0]):
            token = generate_jwt(email)
            return web.json_response({'token': token, 'message': 'Login successful'})
        else:
            return web.json_response({'message': 'Invalid email or password'}, status=401)
    except Exception as e:
        return web.json_response({'message': 'Internal server error'}, status=500)

async def register(request):
    try:
        data = await request.json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password or not name:
            return web.json_response({'message': 'Invalid data'}, status=400)

        hashed_password = bcrypt.hash(password)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)', (email, hashed_password, name))
            conn.commit()
        except sqlite3.IntegrityError:
            return web.json_response({'message': 'Email already in use'}, status=400)
        finally:
            conn.close()

        return web.json_response({'message': 'Registration successful'}, status=201)
    except Exception as e:
        return web.json_response({'message': 'Internal server error'}, status=500)

# Middlewares
@middleware
async def auth_middleware(request, handler):
    if request.path in ['/login', '/register']:
        return await handler(request)

    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        return web.json_response({'message': 'Unauthorized'}, status=401)

    try:
        token_type, token = auth_header.split(' ')
        if token_type.lower() != 'bearer':
            return web.json_response({'message': 'Unauthorized'}, status=401)
        
        email = verify_jwt(token)
        if email:
            request['user_email'] = email
            return await handler(request)
        else:
            return web.json_response({'message': 'Unauthorized'}, status=401)
    except Exception:
        return web.json_response({'message': 'Unauthorized'}, status=401)

# Application setup
app = web.Application(middlewares=[auth_middleware])
app.router.add_post('/login', login)
app.router.add_post('/register', register)

# Initialize the database and run the app
if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)