import os
import json
import sqlite3
import aiohttp
from aiohttp import web
import jwt
from passlib.hash import bcrypt
from aiohttp.web_middlewares import middleware

APP_SECRET = os.environ.get("APP_SECRET", "default_secret")
DATABASE = 'db.sqlite3'

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS merchants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        merchant_id INTEGER,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    )
    ''')
    conn.commit()
    conn.close()

# Middleware to handle exceptions
@middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except web.HTTPException as ex:
        return web.json_response({'error': ex.reason}, status=ex.status)
    except Exception as ex:
        return web.json_response({'error': 'Internal Server Error'}, status=500)

# Middleware to check authorization
@middleware
async def auth_middleware(request, handler):
    if request.path in ['/merchants/register', '/merchants/login'] or request.method == 'GET':
        return await handler(request)
    
    auth_cookie = request.cookies.get('AUTH_COOKIE')
    if not auth_cookie:
        raise web.HTTPUnauthorized(reason='Unauthorized')
    
    try:
        jwt.decode(auth_cookie, APP_SECRET, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        raise web.HTTPUnauthorized(reason='Unauthorized')
    
    return await handler(request)

# Register a new merchant
async def register_merchant(request):
    data = await request.json()
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    
    if not email or not name or not password:
        raise web.HTTPBadRequest(reason='Invalid input')
    
    password_hash = bcrypt.hash(password)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO merchants (email, name, password_hash) VALUES (?, ?, ?)', (email, name, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        raise web.HTTPBadRequest(reason='Email already registered')
    finally:
        conn.close()
    
    return web.Response(status=201, text='Merchant registered successfully')

# Merchant login
async def login_merchant(request):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM merchants WHERE email = ?', (email,))
    merchant = cursor.fetchone()
    conn.close()
    
    if not merchant or not bcrypt.verify(password, merchant[1]):
        raise web.HTTPUnauthorized(reason='Invalid email or password')
    
    token = jwt.encode({'merchant_id': merchant[0]}, APP_SECRET, algorithm='HS256')
    response = web.json_response({'message': 'Login successful'})
    response.set_cookie('AUTH_COOKIE', token)
    return response

# Upload wares
async def upload_wares(request):
    data = await request.json()
    csv_data = data.get('csv')
    
    if not csv_data:
        raise web.HTTPBadRequest(reason='Invalid CSV format')
    
    auth_cookie = request.cookies.get('AUTH_COOKIE')
    payload = jwt.decode(auth_cookie, APP_SECRET, algorithms=['HS256'])
    merchant_id = payload['merchant_id']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        for line in csv_data.splitlines():
            name, description, price = line.split(',')
            cursor.execute('INSERT INTO wares (name, description, price, merchant_id) VALUES (?, ?, ?, ?)', (name, description, float(price), merchant_id))
        conn.commit()
    except Exception as ex:
        raise web.HTTPBadRequest(reason='Invalid CSV format')
    finally:
        conn.close()
    
    return web.Response(status=200, text='Wares uploaded successfully')

# Retrieve wares
async def get_wares(request):
    min_price = request.query.get('minPrice')
    max_price = request.query.get('maxPrice')
    
    query = 'SELECT w.name, w.description, w.price, m.email FROM wares w JOIN merchants m ON w.merchant_id = m.id WHERE 1=1'
    params = []
    
    if min_price:
        query += ' AND w.price >= ?'
        params.append(float(min_price))
    if max_price:
        query += ' AND w.price <= ?'
        params.append(float(max_price))
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    wares = cursor.fetchall()
    conn.close()
    
    html = '<table><tr><th>Name</th><th>Description</th><th>Price</th><th>Merchant Email</th></tr>'
    for ware in wares:
        html += f'<tr><td>{ware[0]}</td><td>{ware[1]}</td><td>{ware[2]}</td><td>{ware[3]}</td></tr>'
    html += '</table>'
    
    return web.Response(content_type='text/html', text=html)

# Main application setup
def create_app():
    init_db()
    app = web.Application(middlewares=[error_middleware, auth_middleware])
    app.router.add_post('/merchants/register', register_merchant)
    app.router.add_post('/merchants/login', login_merchant)
    app.router.add_post('/merchants/upload-wares', upload_wares)
    app.router.add_get('/wares', get_wares)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)