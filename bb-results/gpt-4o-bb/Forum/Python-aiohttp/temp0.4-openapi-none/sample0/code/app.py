import os
import json
import sqlite3
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Handlers
async def get_messages(request: Request) -> Response:
    limit = int(request.query.get('limit', 10))
    offset = int(request.query.get('offset', 0))
    sort = request.query.get('sort', 'DESC').upper()
    
    if sort not in ['ASC', 'DESC']:
        sort = 'DESC'
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f'''
        SELECT username, content, timestamp FROM messages 
        ORDER BY timestamp {sort} 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    messages = c.fetchall()
    conn.close()
    
    message_list = [
        {'username': msg[0], 'content': msg[1], 'timestamp': msg[2]} for msg in messages
    ]
    
    return web.json_response(message_list)

async def post_message(request: Request) -> Response:
    try:
        data = await request.json()
        username = data['username']
        content = data['content']
    except (json.JSONDecodeError, KeyError):
        return web.Response(text='Invalid input', status=400)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (username, content) VALUES (?, ?)
    ''', (username, content))
    conn.commit()
    conn.close()
    
    return web.Response(text='Successful operation', status=200)

# App setup
app = web.Application()
app.router.add_get('/messages', get_messages)
app.router.add_post('/messages', post_message)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)