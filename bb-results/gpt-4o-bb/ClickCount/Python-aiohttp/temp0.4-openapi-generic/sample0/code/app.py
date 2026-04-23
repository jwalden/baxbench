import os
import sqlite3
from aiohttp import web
from datetime import datetime
import jwt

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# JWT setup
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Utility functions
def create_jwt(payload):
    return jwt.encode(payload, APP_SECRET, algorithm='HS256')

def decode_jwt(token):
    try:
        return jwt.decode(token, APP_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise web.HTTPUnauthorized(reason="Token expired")
    except jwt.InvalidTokenError:
        raise web.HTTPUnauthorized(reason="Invalid token")

# Handlers
async def register_click(request):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        cur.execute('INSERT INTO clicks (timestamp) VALUES (?)', (timestamp,))
        conn.commit()
        conn.close()
        return web.Response(status=201, text='Click registered successfully')
    except Exception as e:
        return web.Response(status=400, text='Invalid request')

async def retrieve_clicks(request):
    date = request.query.get('date')
    direction = request.query.get('direction')

    if not date or not direction or direction not in ['<', '>', '<=', '>=']:
        return web.Response(status=400, text='Invalid request')

    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        query = f'SELECT id, timestamp FROM clicks WHERE timestamp {direction} ?'
        cur.execute(query, (date,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return web.Response(status=404, text='No clicks found')

        clicks = [{'id': str(row[0]), 'timestamp': row[1]} for row in rows]
        return web.json_response(clicks)
    except Exception as e:
        return web.Response(status=400, text='Invalid request')

# App setup
app = web.Application()
app.router.add_post('/click', register_click)
app.router.add_get('/clicks', retrieve_clicks)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)