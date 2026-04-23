import os
import sqlite3
import json
from aiohttp import web
from passlib.hash import bcrypt
import jwt
from aiohttp.web_middlewares import middleware

DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'your-secret-key')

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS merchants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        merchant_id INTEGER NOT NULL,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    )
    ''')
    conn.commit()
    conn.close()

@middleware
async def auth_middleware(request, handler):
    if request.path in ['/merchants/upload-wares', '/wares']:
        auth_cookie = request.cookies.get('AUTH_COOKIE')
        if not auth_cookie:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        try:
            jwt.decode(auth_cookie, APP_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        except jwt.InvalidTokenError:
            return web.json_response({'error': 'Unauthorized'}, status=401)
    return await handler(request)

async def register_merchant(request):
    data = await request.json()
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')

    if not email or not name or not password:
        return web.json_response({'error': 'Invalid input'}, status=400)

    hashed_password = bcrypt.hash(password)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO merchants (email, name, password) VALUES (?, ?, ?)', (email, name, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return web.json_response({'error': 'Email already registered'}, status=400)
    finally:
        conn.close()

    return web.json_response({'message': 'Merchant registered successfully'}, status=201)

async def login_merchant(request):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return web.json_response({'error': 'Invalid input'}, status=400)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password FROM merchants WHERE email = ?', (email,))
    merchant = cursor.fetchone()
    conn.close()

    if merchant and bcrypt.verify(password, merchant[1]):
        token = jwt.encode({'merchant_id': merchant[0]}, APP_SECRET, algorithm='HS256')
        response = web.json_response({'message': 'Login successful'})
        response.set_cookie('AUTH_COOKIE', token)
        return response
    else:
        return web.json_response({'error': 'Invalid email or password'}, status=401)

async def upload_wares(request):
    data = await request.json()
    csv_data = data.get('csv')

    if not csv_data:
        return web.json_response({'error': 'Invalid CSV format'}, status=400)

    auth_cookie = request.cookies.get('AUTH_COOKIE')
    merchant_id = jwt.decode(auth_cookie, APP_SECRET, algorithms=['HS256'])['merchant_id']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        for line in csv_data.splitlines():
            name, description, price = line.split(',')
            cursor.execute('INSERT INTO wares (name, description, price, merchant_id) VALUES (?, ?, ?, ?)',
                           (name.strip(), description.strip(), float(price.strip()), merchant_id))
        conn.commit()
    except Exception as e:
        return web.json_response({'error': 'Invalid CSV format'}, status=400)
    finally:
        conn.close()

    return web.json_response({'message': 'Wares uploaded successfully'}, status=200)

async def get_wares(request):
    min_price = request.query.get('minPrice')
    max_price = request.query.get('maxPrice')

    query = 'SELECT wares.name, wares.description, wares.price, merchants.email FROM wares JOIN merchants ON wares.merchant_id = merchants.id WHERE 1=1'
    params = []

    if min_price:
        query += ' AND wares.price >= ?'
        params.append(float(min_price))
    if max_price:
        query += ' AND wares.price <= ?'
        params.append(float(max_price))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    wares = cursor.fetchall()
    conn.close()

    html = "<table><tr><th>Name</th><th>Description</th><th>Price</th><th>Merchant Email</th></tr>"
    for ware in wares:
        html += f"<tr><td>{ware[0]}</td><td>{ware[1]}</td><td>{ware[2]}</td><td>{ware[3]}</td></tr>"
    html += "</table>"

    return web.Response(text=html, content_type='text/html')

app = web.Application(middlewares=[auth_middleware])
app.router.add_post('/merchants/register', register_merchant)
app.router.add_post('/merchants/login', login_merchant)
app.router.add_post('/merchants/upload-wares', upload_wares)
app.router.add_get('/wares', get_wares)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)