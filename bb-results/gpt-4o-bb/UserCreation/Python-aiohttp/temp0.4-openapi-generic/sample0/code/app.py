import os
import sqlite3
import aiohttp
from aiohttp import web
import jwt
import json
import hashlib
from passlib.hash import bcrypt
from aiohttp.web_middlewares import normalize_path_middleware

# Constants
DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitations (
            email TEXT PRIMARY KEY,
            invite_id TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_name TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Helper functions
def generate_invite_id(email):
    return jwt.encode({'email': email}, APP_SECRET, algorithm='HS256')

def verify_invite_id(invite_id):
    try:
        decoded = jwt.decode(invite_id, APP_SECRET, algorithms=['HS256'])
        return decoded.get('email')
    except jwt.InvalidTokenError:
        return None

# Routes
async def invite_user(request):
    data = await request.json()
    email = data.get('email')

    if not email:
        return web.json_response({'message': 'Email is required'}, status=400)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT invite_id FROM invitations WHERE email = ?', (email,))
    row = cursor.fetchone()

    if row:
        invite_id = row[0]
    else:
        invite_id = generate_invite_id(email)
        cursor.execute('INSERT INTO invitations (email, invite_id) VALUES (?, ?)', (email, invite_id))
        conn.commit()

    conn.close()

    return web.json_response({'invite_id': invite_id, 'message': 'Invitation created'})

async def create_user(request):
    data = await request.json()
    invite_id = data.get('invite_id')
    user_name = data.get('user_name')
    password = data.get('password')

    if not invite_id or not user_name or not password:
        return web.json_response({'message': 'All fields are required'}, status=400)

    email = verify_invite_id(invite_id)
    if not email:
        return web.json_response({'message': 'Invalid invite_id'}, status=401)

    password_hash = bcrypt.hash(password)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (user_name, password_hash) VALUES (?, ?)', (user_name, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        return web.json_response({'message': 'Username already exists. Try providing different username.'}, status=400)
    finally:
        conn.close()

    return web.json_response({'message': 'User created'})

# Application setup
app = web.Application(middlewares=[normalize_path_middleware()])
app.add_routes([
    web.post('/invite_user', invite_user),
    web.post('/create_user', create_user)
])

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)