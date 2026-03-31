import os
import jwt
import json
import sqlite3
from aiohttp import web
from datetime import datetime
from passlib.context import CryptContext

# Constants
DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Initialize password context for hashing tokens
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
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

# Helper function to hash tokens
def hash_token(token):
    return pwd_context.hash(token)

# Helper function to verify tokens
def verify_token(token, hashed):
    return pwd_context.verify(token, hashed)

# Middleware to handle exceptions
@web.middleware
async def handle_exceptions(request, handler):
    try:
        response = await handler(request)
        return response
    except web.HTTPException as ex:
        return web.json_response({'error': ex.reason}, status=ex.status)
    except Exception as ex:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Register a heartbeat for a service
async def register_heartbeat(request):
    try:
        data = await request.json()
        service_id = data.get('serviceId')
        token = data.get('token')

        if not service_id or not token:
            return web.json_response({'error': 'Invalid request payload'}, status=400)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Check if service already exists
        cursor.execute('SELECT token FROM services WHERE serviceId = ?', (service_id,))
        row = cursor.fetchone()

        if row:
            # Verify token
            if not verify_token(token, row[0]):
                return web.json_response({'error': 'Unauthorized'}, status=401)
            # Update lastNotification
            cursor.execute('UPDATE services SET lastNotification = ? WHERE serviceId = ?', 
                           (datetime.utcnow().isoformat(), service_id))
        else:
            # Insert new service
            hashed_token = hash_token(token)
            cursor.execute('INSERT INTO services (serviceId, token, lastNotification) VALUES (?, ?, ?)', 
                           (service_id, hashed_token, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()
        return web.json_response({'message': 'Heartbeat registered successfully'}, status=200)
    except Exception as e:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Get overview of registered services
async def get_services(request):
    try:
        data = await request.json()
        token = data.get('token')

        if not token:
            return web.json_response({'error': 'Invalid request payload'}, status=400)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Retrieve services with matching token
        cursor.execute('SELECT serviceId, lastNotification, token FROM services')
        services = []
        for row in cursor.fetchall():
            service_id, last_notification, stored_token = row
            if verify_token(token, stored_token):
                services.append({
                    'serviceId': service_id,
                    'lastNotification': last_notification
                })

        conn.close()
        return web.json_response(services, status=200)
    except Exception as e:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Initialize app and routes
app = web.Application(middlewares=[handle_exceptions])
app.router.add_post('/heartbeat', register_heartbeat)
app.router.add_post('/services', get_services)

# Initialize database and run the app
init_db()
web.run_app(app, host='0.0.0.0', port=5000)