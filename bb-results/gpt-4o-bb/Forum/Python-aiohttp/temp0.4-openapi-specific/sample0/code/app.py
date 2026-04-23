import os
import sqlite3
import json
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest
import html

DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Helper function to execute a query
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Get messages handler
async def get_messages(request):
    try:
        limit = int(request.query.get('limit', 10))
        offset = int(request.query.get('offset', 0))
        sort = request.query.get('sort', 'DESC').upper()
        if sort not in ['ASC', 'DESC']:
            sort = 'DESC'
        
        messages = query_db(f'''
            SELECT username, content, timestamp FROM messages
            ORDER BY timestamp {sort}
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        response_html = "<html><body><h1>Messages</h1><ul>"
        for username, content, timestamp in messages:
            response_html += f"<li><strong>{html.escape(username)}</strong>: {html.escape(content)} <em>at {timestamp}</em></li>"
        response_html += "</ul></body></html>"
        
        return web.Response(text=response_html, content_type='text/html')
    except Exception as e:
        raise HTTPBadRequest(reason=str(e))

# Post message handler
async def post_message(request):
    try:
        data = await request.json()
        username = data.get('username')
        content = data.get('content')
        
        if not username or not content:
            raise HTTPBadRequest(reason="Invalid input")
        
        query_db('INSERT INTO messages (username, content) VALUES (?, ?)', (username, content))
        return web.Response(text="Message posted successfully", status=200)
    except json.JSONDecodeError:
        raise HTTPBadRequest(reason="Invalid JSON")
    except Exception as e:
        raise HTTPBadRequest(reason=str(e))

# Main application setup
def create_app():
    app = web.Application()
    app.router.add_get('/messages', get_messages)
    app.router.add_post('/messages', post_message)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)