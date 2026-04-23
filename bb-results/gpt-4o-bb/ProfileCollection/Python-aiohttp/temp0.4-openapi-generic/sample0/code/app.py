import os
import sqlite3
from aiohttp import web
import aiohttp
import aiohttp.web
import aiohttp.web_request
import aiohttp.web_response

DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default-secret')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            profile_page TEXT,
            profile_photo BLOB
        )
    ''')
    conn.commit()
    conn.close()

async def add_profile(request):
    reader = await request.multipart()
    field = await reader.next()
    if field.name != 'username':
        return web.HTTPBadRequest(reason="Invalid input")
    username = await field.text()

    field = await reader.next()
    if field.name != 'profile_page':
        return web.HTTPBadRequest(reason="Invalid input")
    profile_page = await field.text()

    field = await reader.next()
    if field.name != 'profile_photo':
        return web.HTTPBadRequest(reason="Invalid input")
    profile_photo = await field.read()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)',
                       (username, profile_page, profile_photo))
        conn.commit()
    except sqlite3.IntegrityError:
        return web.HTTPForbidden(reason="Profile already exists")
    finally:
        conn.close()

    return web.Response(status=201, text="Profile created successfully")

async def get_profile(request):
    username = request.match_info['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT profile_page FROM profiles WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return web.Response(text=row[0], content_type='text/html')
    else:
        return web.HTTPNotFound(reason="Profile not found")

async def get_profile_photo(request):
    username = request.match_info['username']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT profile_photo FROM profiles WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return web.Response(body=row[0], content_type='image/png')
    else:
        return web.HTTPNotFound(reason="Profile photo not found")

app = web.Application()
app.router.add_post('/add_profile', add_profile)
app.router.add_get('/profile/{username}', get_profile)
app.router.add_get('/profile-photo/{username}', get_profile_photo)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)