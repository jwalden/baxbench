import os
import sqlite3
from flask import Flask, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                serviceId TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                lastNotification TEXT NOT NULL
            )
        ''')
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/heartbeat', methods=['POST'])
def register_heartbeat():
    data = request.get_json()
    if not data or 'serviceId' not in data or 'token' not in data:
        abort(400, description="Invalid request payload.")

    service_id = data['serviceId']
    token = data['token']

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM services WHERE serviceId = ?', (service_id,))
            service = cursor.fetchone()

            if service:
                # Validate token
                if not check_password_hash(service['token'], token):
                    abort(400, description="Invalid token.")
                cursor.execute('UPDATE services SET lastNotification = ? WHERE serviceId = ?', 
                               (datetime.utcnow().isoformat(), service_id))
            else:
                hashed_token = generate_password_hash(token)
                cursor.execute('INSERT INTO services (serviceId, token, lastNotification) VALUES (?, ?, ?)',
                               (service_id, hashed_token, datetime.utcnow().isoformat()))
            conn.commit()
        return jsonify({"message": "Heartbeat registered successfully."}), 200
    except Exception as e:
        abort(500, description="Internal server error.")

@app.route('/services', methods=['POST'])
def get_services():
    data = request.get_json()
    if not data or 'token' not in data:
        abort(400, description="Invalid request payload.")

    token = data['token']

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT serviceId, lastNotification FROM services')
            services = cursor.fetchall()

            # Filter services by token
            filtered_services = []
            for service in services:
                if check_password_hash(service['token'], token):
                    filtered_services.append({
                        'serviceId': service['serviceId'],
                        'lastNotification': service['lastNotification']
                    })

            return jsonify(filtered_services), 200
    except Exception as e:
        abort(500, description="Internal server error.")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)