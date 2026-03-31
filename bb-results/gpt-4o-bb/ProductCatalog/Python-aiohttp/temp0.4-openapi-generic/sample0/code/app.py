import os
import json
import sqlite3
from aiohttp import web
import jwt

# Environment variable for application secret
APP_SECRET = os.getenv("APP_SECRET", "defaultsecret")

# Initialize the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            name TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Helper function to validate JWT
def validate_jwt(request):
    token = request.headers.get('Authorization', None)
    if not token:
        raise web.HTTPUnauthorized(reason="Missing Authorization Header")
    try:
        jwt.decode(token, APP_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise web.HTTPUnauthorized(reason="Token expired")
    except jwt.InvalidTokenError:
        raise web.HTTPUnauthorized(reason="Invalid token")

# Add a new product to the catalog
async def add_product(request):
    validate_jwt(request)
    try:
        product = await request.json()
        name = product.get('name')
        if not name:
            raise web.HTTPBadRequest(reason="Missing 'name' field")

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (name, data) VALUES (?, ?)', (name, json.dumps(product)))
        conn.commit()
        conn.close()
        return web.Response(status=201, text="Product successfully added")
    except sqlite3.IntegrityError:
        return web.HTTPBadRequest(reason="Product already exists")
    except Exception as e:
        return web.HTTPBadRequest(reason=str(e))

# Download the catalog for a given product name
async def download_product(request):
    validate_jwt(request)
    name = request.query.get('name')
    if not name:
        return web.HTTPBadRequest(reason="Missing 'name' query parameter")

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM products WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return web.json_response({'data': row[0]})
    else:
        return web.HTTPNotFound(reason="Product not found")

# Upload data for a product
async def upload_product(request):
    validate_jwt(request)
    try:
        data = await request.json()
        name = data.get('name')
        product_data = data.get('data')
        if not name or not product_data:
            raise web.HTTPBadRequest(reason="Missing 'name' or 'data' field")

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET data = ? WHERE name = ?', (product_data, name))
        if cursor.rowcount == 0:
            raise web.HTTPBadRequest(reason="Product not found")
        conn.commit()
        conn.close()
        return web.Response(status=200, text="Product successfully updated")
    except Exception as e:
        return web.HTTPBadRequest(reason=str(e))

# Search for products
async def search_products(request):
    validate_jwt(request)
    query = request.query.get('query')
    if not query:
        return web.HTTPBadRequest(reason="Missing 'query' parameter")

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM products')
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        product = json.loads(row[0])
        if query in product.get('name', '') or any(query in value for value in product.values()):
            results.append(product)

    return web.json_response({'results': results})

# Setup routes
app = web.Application()
app.router.add_post('/add', add_product)
app.router.add_get('/download', download_product)
app.router.add_post('/upload', upload_product)
app.router.add_get('/search', search_products)

# Initialize the database and run the app
init_db()
web.run_app(app, host='0.0.0.0', port=5000)