import os
import sqlite3
import uuid
from aiohttp import web
from passlib.hash import bcrypt
import jwt
import json

APP_SECRET = os.getenv("APP_SECRET", "your_secret_key")

DATABASE = 'db.sqlite3'

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
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

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
        invite_id = str(uuid.uuid4())
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

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM invitations WHERE invite_id = ?', (invite_id,))
    row = cursor.fetchone()

    if not row:
        return web.json_response({'message': 'Invalid invite_id'}, status=401)

    cursor.execute('SELECT user_name FROM users WHERE user_name = ?', (user_name,))
    if cursor.fetchone():
        return web.json_response({'message': 'Username already exists. Try providing different username.'}, status=400)

    hashed_password = bcrypt.hash(password)
    cursor.execute('INSERT INTO users (user_name, password) VALUES (?, ?)', (user_name, hashed_password))
    conn.commit()

    conn.close()
    return web.json_response({'message': 'User created'})

app = web.Application()
app.router.add_post('/invite_user', invite_user)
app.router.add_post('/create_user', create_user)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)