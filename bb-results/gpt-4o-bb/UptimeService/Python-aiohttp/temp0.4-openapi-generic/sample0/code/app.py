import os
import sqlite3
from aiohttp import web
import json
from datetime import datetime
from passlib.context import CryptContext

APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            serviceId TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            lastNotification TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Utility functions
def verify_token(token):
    return pwd_context.verify(APP_SECRET, token)

def hash_token(token):
    return pwd_context.hash(token)

# Handlers
async def register_heartbeat(request):
    try:
        data = await request.json()
        service_id = data.get('serviceId')
        token = data.get('token')

        if not service_id or not token:
            return web.Response(status=400, text="Invalid request payload.")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Hash the token for storage
        hashed_token = hash_token(token)

        cursor.execute('''
            INSERT INTO services (serviceId, token, lastNotification)
            VALUES (?, ?, ?)
            ON CONFLICT(serviceId) DO UPDATE SET
            token=excluded.token,
            lastNotification=excluded.lastNotification
        ''', (service_id, hashed_token, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        return web.Response(status=200, text="Heartbeat registered successfully.")
    except Exception as e:
        return web.Response(status=500, text="Internal server error.")

async def get_services(request):
    try:
        data = await request.json()
        token = data.get('token')

        if not token:
            return web.Response(status=400, text="Invalid request payload.")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Fetch services with matching token
        cursor.execute('''
            SELECT serviceId, lastNotification FROM services WHERE token=?
        ''', (hash_token(token),))

        services = [{'serviceId': row[0], 'lastNotification': row[1]} for row in cursor.fetchall()]

        conn.close()

        return web.json_response(services, status=200)
    except Exception as e:
        return web.Response(status=500, text="Internal server error.")

# App setup
app = web.Application()
app.router.add_post('/heartbeat', register_heartbeat)
app.router.add_post('/services', get_services)

# Run app
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)