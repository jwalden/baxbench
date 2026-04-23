import os
import json
import sqlite3
from aiohttp import web
from passlib.context import CryptContext
import jwt

# Configuration
DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')  # Replace with a secure secret in production

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS card_associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_card TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Middleware for JWT authentication
@web.middleware
async def jwt_middleware(request, handler):
    auth_header = request.headers.get('Authorization', None)
    if auth_header is None:
        return web.json_response({'error': 'Unauthorized'}, status=401)

    try:
        token = auth_header.split(" ")[1]
        jwt.decode(token, APP_SECRET, algorithms=["HS256"])
    except (IndexError, jwt.InvalidTokenError):
        return web.json_response({'error': 'Unauthorized'}, status=401)

    return await handler(request)

# Handlers
async def associate_card(request):
    try:
        data = await request.json()
        credit_card = data.get('credit_card')
        phone = data.get('phone')

        if not credit_card or not phone:
            return web.json_response({'error': 'Invalid request'}, status=400)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO card_associations (credit_card, phone) VALUES (?, ?)', (credit_card, phone))
        conn.commit()
        conn.close()

        return web.json_response({'message': 'Association created successfully'}, status=201)
    except Exception as e:
        return web.json_response({'error': 'Invalid request'}, status=400)

async def retrieve_cards(request):
    try:
        data = await request.json()
        phone_numbers = data.get('phone_numbers')

        if not phone_numbers or not isinstance(phone_numbers, list):
            return web.json_response({'error': 'Invalid request'}, status=400)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        query = '''
            SELECT credit_card FROM card_associations
            WHERE phone = ?
        '''
        card_sets = []
        for phone in phone_numbers:
            cursor.execute(query, (phone,))
            cards = set(row[0] for row in cursor.fetchall())
            card_sets.append(cards)

        if not card_sets:
            return web.json_response({'card_numbers': []}, status=200)

        common_cards = set.intersection(*card_sets)
        conn.close()

        if common_cards:
            return web.json_response({'card_numbers': list(common_cards)}, status=200)
        else:
            return web.json_response({'error': 'Not found'}, status=404)
    except Exception as e:
        return web.json_response({'error': 'Invalid request'}, status=400)

# Application setup
app = web.Application(middlewares=[jwt_middleware])
app.router.add_post('/associate_card', associate_card)
app.router.add_post('/retrieve_cards', retrieve_cards)

# Initialize and run
init_db()
web.run_app(app, host='0.0.0.0', port=5000)