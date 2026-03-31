import os
import sqlite3
from aiohttp import web
from datetime import datetime
import json

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Helper functions
def register_click():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO clicks (timestamp) VALUES (?)', (timestamp,))
    conn.commit()
    conn.close()
    return timestamp

def retrieve_clicks(date, direction):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = f'SELECT id, timestamp FROM clicks WHERE timestamp {direction} ?'
    cursor.execute(query, (date,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': str(row[0]), 'timestamp': row[1]} for row in rows]

# Request handlers
async def handle_register_click(request):
    try:
        timestamp = register_click()
        return web.Response(status=201, text=f'Click registered at {timestamp}')
    except Exception as e:
        return web.Response(status=400, text=str(e))

async def handle_retrieve_clicks(request):
    try:
        date = request.query.get('date')
        direction = request.query.get('direction')
        if not date or not direction:
            raise ValueError("Both 'date' and 'direction' query parameters are required.")
        
        clicks = retrieve_clicks(date, direction)
        if not clicks:
            return web.Response(status=404, text='No clicks found')
        
        return web.json_response(clicks)
    except ValueError as ve:
        return web.Response(status=400, text=str(ve))
    except Exception as e:
        return web.Response(status=400, text=str(e))

# App setup
app = web.Application()
app.router.add_post('/click', handle_register_click)
app.router.add_get('/clicks', handle_retrieve_clicks)

# Run app
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)