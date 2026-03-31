import os
import sqlite3
import uuid
from aiohttp import web
import json
from passlib.hash import bcrypt
import jwt
from aiohttp.web import HTTPBadRequest, HTTPUnauthorized

APP_SECRET = os.environ.get("APP_SECRET", "default_secret")

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
    try:
        data = await request.json()
        email = data['email']
    except (json.JSONDecodeError, KeyError):
        raise HTTPBadRequest(text='Invalid request body')

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
    try:
        data = await request.json()
        invite_id = data['invite_id']
        user_name = data['user_name']
        password = data['password']
    except (json.JSONDecodeError, KeyError):
        raise HTTPBadRequest(text='Invalid request body')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM invitations WHERE invite_id = ?', (invite_id,))
    row = cursor.fetchone()

    if not row:
        raise HTTPUnauthorized(text='Invalid invite_id')

    cursor.execute('SELECT user_name FROM users WHERE user_name = ?', (user_name,))
    if cursor.fetchone():
        raise HTTPBadRequest(text='Username already exists. Try providing different username.')

    hashed_password = bcrypt.hash(password)
    cursor.execute('INSERT INTO users (user_name, password) VALUES (?, ?)', (user_name, hashed_password))
    conn.commit()
    conn.close()

    return web.json_response({'message': 'User created'})

def create_app():
    init_db()
    app = web.Application()
    app.router.add_post('/invite_user', invite_user)
    app.router.add_post('/create_user', create_user)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)