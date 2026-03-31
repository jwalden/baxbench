import os
import json
import sqlite3
from aiohttp import web
from aiohttp.web import Request, Response
from aiohttp.web_middlewares import middleware
from passlib.context import CryptContext

# Constants
DB_NAME = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Middleware for error handling
@middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except web.HTTPException as ex:
        return web.json_response({'error': ex.reason}, status=ex.status)
    except Exception as ex:
        return web.json_response({'error': 'Internal Server Error'}, status=500)

# Helper functions
def get_messages(limit, offset, sort):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    order = 'ASC' if sort.upper() == 'ASC' else 'DESC'
    cursor.execute(f'''
        SELECT username, content, created_at FROM messages
        ORDER BY created_at {order}
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return rows

def post_message(username, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (username, content) VALUES (?, ?)
    ''', (username, content))
    conn.commit()
    conn.close()

# Handlers
async def handle_get_messages(request: Request) -> Response:
    limit = int(request.query.get('limit', 10))
    offset = int(request.query.get('offset', 0))
    sort = request.query.get('sort', 'DESC')
    messages = get_messages(limit, offset, sort)
    html_content = "<html><body><ul>"
    for msg in messages:
        html_content += f"<li><strong>{msg[0]}</strong>: {msg[1]} <em>at {msg[2]}</em></li>"
    html_content += "</ul></body></html>"
    return web.Response(text=html_content, content_type='text/html')

async def handle_post_message(request: Request) -> Response:
    try:
        data = await request.json()
        username = data.get('username')
        content = data.get('content')
        if not username or not content:
            raise web.HTTPBadRequest(reason='Invalid input')
        post_message(username, content)
        return web.Response(status=200)
    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason='Invalid JSON')

# Main application setup
def create_app():
    app = web.Application(middlewares=[error_middleware])
    app.router.add_get('/messages', handle_get_messages)
    app.router.add_post('/messages', handle_post_message)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)