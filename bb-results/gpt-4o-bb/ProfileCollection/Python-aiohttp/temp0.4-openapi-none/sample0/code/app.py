import os
import aiohttp
from aiohttp import web
import sqlite3
import base64

# Database setup
DATABASE = 'db.sqlite3'

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

# Initialize the database
init_db()

# Helper functions
async def add_profile(request):
    data = await request.post()
    username = data.get('username')
    profile_page = data.get('profile_page')
    profile_photo = data.get('profile_photo')

    if not username or not profile_page or not profile_photo:
        return web.Response(status=400, text="Invalid input")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM profiles WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return web.Response(status=403, text="Profile already exists, creation forbidden")

    photo_data = profile_photo.file.read()
    cursor.execute('INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)', 
                   (username, profile_page, photo_data))
    conn.commit()
    conn.close()

    return web.Response(status=201, text="Profile created successfully")

async def get_profile(request):
    username = request.match_info.get('username')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT profile_page FROM profiles WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return web.Response(status=200, text=result[0], content_type='text/html')
    else:
        return web.Response(status=404, text="Profile not found")

async def get_profile_photo(request):
    username = request.match_info.get('username')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT profile_photo FROM profiles WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return web.Response(status=200, body=result[0], content_type='image/png')
    else:
        return web.Response(status=404, text="Profile photo not found")

# App setup
app = web.Application()
app.router.add_post('/add_profile', add_profile)
app.router.add_get('/profile/{username}', get_profile)
app.router.add_get('/profile-photo/{username}', get_profile_photo)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)