import os
import aiohttp
from aiohttp import web
import sqlite3
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound, HTTPForbidden
import base64

# Database setup
DATABASE = 'db.sqlite3'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        username TEXT PRIMARY KEY,
        profile_page TEXT NOT NULL,
        profile_photo BLOB NOT NULL
    )
''')
conn.commit()

# Helper function to get profile
def get_profile(username):
    cursor.execute('SELECT profile_page, profile_photo FROM profiles WHERE username = ?', (username,))
    return cursor.fetchone()

# Routes
async def add_profile(request: Request) -> Response:
    try:
        data = await request.post()
        username = data.get('username')
        profile_page = data.get('profile_page')
        profile_photo = data.get('profile_photo')

        if not username or not profile_page or not profile_photo:
            raise HTTPBadRequest(reason="Invalid input")

        if get_profile(username):
            raise HTTPForbidden(reason="Profile already exists")

        profile_photo_data = profile_photo.file.read()
        cursor.execute('INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)',
                       (username, profile_page, profile_photo_data))
        conn.commit()
        return web.Response(text="Profile created successfully", status=201)

    except Exception as e:
        raise HTTPBadRequest(reason=str(e))

async def get_profile_page(request: Request) -> Response:
    username = request.match_info.get('username')
    profile = get_profile(username)
    if profile:
        profile_page, _ = profile
        return web.Response(text=profile_page, content_type='text/html')
    else:
        raise HTTPNotFound(reason="Profile not found")

async def get_profile_photo(request: Request) -> Response:
    username = request.match_info.get('username')
    profile = get_profile(username)
    if profile:
        _, profile_photo = profile
        return web.Response(body=profile_photo, content_type='image/png')
    else:
        raise HTTPNotFound(reason="Profile photo not found")

# App setup
app = web.Application()
app.router.add_post('/add_profile', add_profile)
app.router.add_get('/profile/{username}', get_profile_page)
app.router.add_get('/profile-photo/{username}', get_profile_photo)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)