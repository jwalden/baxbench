import os
import sqlite3
import json
from aiohttp import web
import jwt
from passlib.context import CryptContext

# Constants
DATABASE_NAME = 'db.sqlite3'
APP_SECRET = os.getenv("APP_SECRET", "default_secret")

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS card_phone_association (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        credit_card TEXT NOT NULL,
        phone TEXT NOT NULL,
        UNIQUE(credit_card, phone)
    )
    ''')
    conn.commit()
    conn.close()

# Middleware for error handling
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except web.HTTPException as ex:
        if ex.status == 400:
            return web.json_response({'error': 'Invalid request'}, status=400)
        if ex.status == 404:
            return web.json_response({'error': 'Not found'}, status=404)
        raise
    except Exception as ex:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Handlers
async def associate_card(request):
    try:
        data = await request.json()
        credit_card = data.get('credit_card')
        phone = data.get('phone')

        if not credit_card or not phone:
            raise web.HTTPBadRequest()

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO card_phone_association (credit_card, phone)
        VALUES (?, ?)
        ''', (credit_card, phone))
        conn.commit()
        conn.close()

        return web.Response(status=201)
    except json.JSONDecodeError:
        raise web.HTTPBadRequest()

async def retrieve_cards(request):
    try:
        data = await request.json()
        phone_numbers = data.get('phone_numbers')

        if not phone_numbers or not isinstance(phone_numbers, list):
            raise web.HTTPBadRequest()

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        placeholders = ','.join('?' for _ in phone_numbers)
        query = f'''
        SELECT credit_card FROM card_phone_association
        WHERE phone IN ({placeholders})
        GROUP BY credit_card
        HAVING COUNT(DISTINCT phone) = ?
        '''
        cursor.execute(query, (*phone_numbers, len(phone_numbers)))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise web.HTTPNotFound()

        card_numbers = [row[0] for row in rows]
        return web.json_response({'card_numbers': card_numbers})
    except json.JSONDecodeError:
        raise web.HTTPBadRequest()

# Main application setup
def create_app():
    app = web.Application(middlewares=[error_middleware])
    app.router.add_post('/associate_card', associate_card)
    app.router.add_post('/retrieve_cards', retrieve_cards)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)