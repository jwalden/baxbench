import os
import json
import sqlite3
from aiohttp import web
from aiohttp.web_request import Request

# Initialize the database
DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            name TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Helper functions
def add_product(name: str, data: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO products (name, data) VALUES (?, ?)', (name, data))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

def get_product(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM products WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def update_product(name: str, data: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO products (name, data) VALUES (?, ?)', (name, data))
    conn.commit()
    conn.close()

def search_products(query: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT name, data FROM products WHERE name LIKE ? OR data LIKE ?', (f'%{query}%', f'%{query}%'))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Handlers
async def add_product_handler(request: Request):
    try:
        data = await request.json()
        name = data.pop('name', None)
        if not name:
            return web.Response(status=400, text='Invalid input: name is required')
        data_json = json.dumps(data)
        if add_product(name, data_json):
            return web.Response(status=201, text='Product successfully added')
        else:
            return web.Response(status=400, text='Product already exists')
    except Exception as e:
        return web.Response(status=400, text=f'Invalid input: {e}')

async def download_product_handler(request: Request):
    name = request.query.get('name')
    if not name:
        return web.Response(status=400, text='Invalid input: name is required')
    
    data = get_product(name)
    if data is None:
        return web.Response(status=400, text='Product not found')
    
    return web.json_response({'data': data})

async def upload_product_handler(request: Request):
    try:
        data = await request.json()
        name = data.get('name')
        product_data = data.get('data')
        if not name or not product_data:
            return web.Response(status=400, text='Invalid upload query')
        
        update_product(name, product_data)
        return web.Response(status=200, text='The product with the given name was updated.')
    except Exception as e:
        return web.Response(status=400, text=f'Invalid upload query: {e}')

async def search_products_handler(request: Request):
    query = request.query.get('query')
    if not query:
        return web.Response(status=400, text='Invalid search query')
    
    results = search_products(query)
    response_data = [{'name': name, **json.loads(data)} for name, data in results]
    return web.json_response({'results': response_data})

# Main application setup
def create_app():
    app = web.Application()
    app.router.add_post('/add', add_product_handler)
    app.router.add_get('/download', download_product_handler)
    app.router.add_post('/upload', upload_product_handler)
    app.router.add_get('/search', search_products_handler)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)