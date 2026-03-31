import os
import json
import sqlite3
from aiohttp import web
from aiohttp.web import HTTPBadRequest, HTTPInternalServerError
import jwt

DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'your_default_secret')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

async def add_product(request):
    try:
        data = await request.json()
        name = data.get('name')
        if not name:
            raise HTTPBadRequest(reason="Name is required")

        additional_properties = {k: v for k, v in data.items() if k != 'name'}
        product_data = json.dumps(additional_properties)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (name, data) VALUES (?, ?)', (name, product_data))
        conn.commit()
        conn.close()

        return web.Response(status=201)
    except sqlite3.IntegrityError:
        raise HTTPBadRequest(reason="Product already exists")
    except Exception as e:
        raise HTTPInternalServerError(reason=str(e))

async def download_product(request):
    name = request.query.get('name')
    if not name:
        raise HTTPBadRequest(reason="Name query parameter is required")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM products WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return web.json_response({'data': row[0]})
    else:
        raise HTTPBadRequest(reason="Product not found")

async def upload_product(request):
    try:
        data = await request.json()
        name = data.get('name')
        product_data = data.get('data')

        if not name or not product_data:
            raise HTTPBadRequest(reason="Name and data are required")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET data = ? WHERE name = ?', (product_data, name))
        if cursor.rowcount == 0:
            raise HTTPBadRequest(reason="Product not found")
        conn.commit()
        conn.close()

        return web.Response(status=200)
    except Exception as e:
        raise HTTPInternalServerError(reason=str(e))

async def search_products(request):
    query = request.query.get('query')
    if not query:
        raise HTTPBadRequest(reason="Query parameter is required")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT name, data FROM products')
    rows = cursor.fetchall()
    conn.close()

    results = []
    for name, data in rows:
        product_data = json.loads(data)
        if query in name or any(query in value for value in product_data.values()):
            results.append({'name': name, **product_data})

    return web.json_response({'results': results})

app = web.Application()
app.router.add_post('/add', add_product)
app.router.add_get('/download', download_product)
app.router.add_post('/upload', upload_product)
app.router.add_get('/search', search_products)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)