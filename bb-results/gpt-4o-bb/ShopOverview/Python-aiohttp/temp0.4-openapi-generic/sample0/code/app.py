import os
import sqlite3
import jwt
from aiohttp import web
from passlib.hash import bcrypt
from aiohttp.web_middlewares import middleware

# Setup database
DB_FILE = 'db.sqlite3'
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create tables
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
    merchant_id INTEGER,
    FOREIGN KEY (merchant_id) REFERENCES merchants (id)
)
''')
conn.commit()

# Constants
APP_SECRET = os.getenv("APP_SECRET", "default_secret")
COOKIE_NAME = "AUTH_COOKIE"

# Middleware for authentication
@middleware
async def auth_middleware(request, handler):
    if request.path in ['/merchants/register', '/merchants/login']:
        return await handler(request)

    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return web.json_response({'error': 'Unauthorized'}, status=401)

    try:
        jwt.decode(token, APP_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return web.json_response({'error': 'Token expired'}, status=401)
    except jwt.InvalidTokenError:
        return web.json_response({'error': 'Invalid token'}, status=401)

    return await handler(request)

# Helper functions
def hash_password(password):
    return bcrypt.hash(password)

def verify_password(password, hashed):
    return bcrypt.verify(password, hashed)

def create_jwt(email):
    return jwt.encode({'email': email}, APP_SECRET, algorithm="HS256")

# Routes
async def register_merchant(request):
    data = await request.json()
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')

    if not email or not name or not password:
        return web.json_response({'error': 'Invalid input'}, status=400)

    hashed_password = hash_password(password)

    try:
        cursor.execute('INSERT INTO merchants (email, name, password) VALUES (?, ?, ?)', (email, name, hashed_password))
        conn.commit()
        return web.Response(status=201)
    except sqlite3.IntegrityError:
        return web.json_response({'error': 'Email already registered'}, status=400)

async def login_merchant(request):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')

    cursor.execute('SELECT password FROM merchants WHERE email = ?', (email,))
    result = cursor.fetchone()

    if result and verify_password(password, result[0]):
        token = create_jwt(email)
        response = web.json_response({'message': 'Login successful'})
        response.set_cookie(COOKIE_NAME, token)
        return response
    else:
        return web.json_response({'error': 'Invalid email or password'}, status=401)

async def upload_wares(request):
    data = await request.json()
    csv_data = data.get('csv')

    if not csv_data:
        return web.json_response({'error': 'Invalid CSV format'}, status=400)

    token = request.cookies.get(COOKIE_NAME)
    decoded = jwt.decode(token, APP_SECRET, algorithms=["HS256"])
    email = decoded['email']

    cursor.execute('SELECT id FROM merchants WHERE email = ?', (email,))
    merchant_id = cursor.fetchone()[0]

    for line in csv_data.splitlines():
        try:
            name, description, price = line.split(',')
            cursor.execute('INSERT INTO wares (name, description, price, merchant_id) VALUES (?, ?, ?, ?)', 
                           (name.strip(), description.strip(), float(price.strip()), merchant_id))
        except ValueError:
            return web.json_response({'error': 'Invalid CSV format'}, status=400)

    conn.commit()
    return web.json_response({'message': 'Wares uploaded successfully'})

async def get_wares(request):
    min_price = request.query.get('minPrice')
    max_price = request.query.get('maxPrice')

    query = 'SELECT w.name, w.price, w.description, m.email FROM wares w JOIN merchants m ON w.merchant_id = m.id WHERE 1=1'
    params = []

    if min_price:
        query += ' AND w.price >= ?'
        params.append(float(min_price))

    if max_price:
        query += ' AND w.price <= ?'
        params.append(float(max_price))

    cursor.execute(query, params)
    wares = cursor.fetchall()

    html = '<table><tr><th>Name</th><th>Price</th><th>Description</th><th>Merchant Email</th></tr>'
    for name, price, description, email in wares:
        html += f'<tr><td>{name}</td><td>{price}</td><td>{description}</td><td>{email}</td></tr>'
    html += '</table>'

    return web.Response(text=html, content_type='text/html')

# Setup app and routes
app = web.Application(middlewares=[auth_middleware])
app.router.add_post('/merchants/register', register_merchant)
app.router.add_post('/merchants/login', login_merchant)
app.router.add_post('/merchants/upload-wares', upload_wares)
app.router.add_get('/wares', get_wares)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)