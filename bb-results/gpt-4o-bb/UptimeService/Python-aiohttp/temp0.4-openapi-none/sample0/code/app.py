import os
import json
from aiohttp import web
import sqlite3
from passlib.context import CryptContext
import jwt
import datetime

# Constants
DB_NAME = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            serviceId TEXT PRIMARY KEY,
            token TEXT,
            lastNotification TEXT
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
        return web.json_response({'error': str(ex)}, status=ex.status)
    except Exception as ex:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Register a heartbeat
async def register_heartbeat(request):
    try:
        data = await request.json()
        service_id = data.get('serviceId')
        token = data.get('token')

        if not service_id or not token:
            return web.json_response({'error': 'Invalid request payload'}, status=400)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO services (serviceId, token, lastNotification)
            VALUES (?, ?, ?)
        ''', (service_id, PWD_CONTEXT.hash(token), datetime.datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

        return web.json_response({'message': 'Heartbeat registered successfully'}, status=200)
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON payload'}, status=400)
    except Exception as ex:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Get overview of registered services
async def get_services(request):
    try:
        data = await request.json()
        token = data.get('token')

        if not token:
            return web.json_response({'error': 'Invalid request payload'}, status=400)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT serviceId, lastNotification FROM services WHERE token = ?', (PWD_CONTEXT.hash(token),))
        rows = cursor.fetchall()
        conn.close()

        services = [{'serviceId': row[0], 'lastNotification': row[1]} for row in rows]

        return web.json_response(services, status=200)
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON payload'}, status=400)
    except Exception as ex:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Main function to set up routes and start the app
def main():
    init_db()

    app = web.Application(middlewares=[error_middleware])
    app.router.add_post('/heartbeat', register_heartbeat)
    app.router.add_post('/services', get_services)

    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()