import os
import jwt
import sqlite3
from aiohttp import web
from passlib.hash import bcrypt
from aiohttp.web_middlewares import middleware

APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

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

async def login(request):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return web.json_response({'message': 'Invalid email or password'}, status=401)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.verify(password, user[1]):
        token = jwt.encode({'id': user[0]}, APP_SECRET, algorithm='HS256')
        return web.json_response({'token': token, 'message': 'Login successful'}, status=200)
    else:
        return web.json_response({'message': 'Invalid email or password'}, status=401)

async def register(request):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return web.json_response({'message': 'Invalid data'}, status=400)

    hashed_password = bcrypt.hash(password)

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)', (email, hashed_password, name))
        conn.commit()
        conn.close()
        return web.json_response({'message': 'Registration successful'}, status=201)
    except sqlite3.IntegrityError:
        return web.json_response({'message': 'Email already in use'}, status=400)

@middleware
async def auth_middleware(request, handler):
    if request.path in ['/login', '/register']:
        return await handler(request)

    auth_header = request.headers.get('Authorization', None)
    if auth_header is None or not auth_header.startswith('Bearer '):
        return web.json_response({'message': 'Unauthorized'}, status=401)

    token = auth_header.split(' ')[1]
    try:
        jwt.decode(token, APP_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return web.json_response({'message': 'Token expired'}, status=401)
    except jwt.InvalidTokenError:
        return web.json_response({'message': 'Invalid token'}, status=401)

    return await handler(request)

def create_app():
    app = web.Application(middlewares=[auth_middleware])
    app.router.add_post('/login', login)
    app.router.add_post('/register', register)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)