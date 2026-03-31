import os
import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Database setup
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

init_db()

# Helper functions
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def verify_token(stored_token, provided_token):
    return check_password_hash(stored_token, provided_token)

@app.route('/heartbeat', methods=['POST'])
def register_heartbeat():
    data = request.get_json()
    if not data or 'serviceId' not in data or 'token' not in data:
        return jsonify({'error': 'Invalid request payload.'}), 400

    service_id = data['serviceId']
    token = data['token']

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT token FROM services WHERE serviceId = ?', (service_id,))
            row = cursor.fetchone()

            if row:
                stored_token = row['token']
                if not verify_token(stored_token, token):
                    return jsonify({'error': 'Unauthorized.'}), 400

                cursor.execute('''
                    UPDATE services
                    SET lastNotification = ?
                    WHERE serviceId = ?
                ''', (datetime.utcnow().isoformat(), service_id))
            else:
                hashed_token = generate_password_hash(token)
                cursor.execute('''
                    INSERT INTO services (serviceId, token, lastNotification)
                    VALUES (?, ?, ?)
                ''', (service_id, hashed_token, datetime.utcnow().isoformat()))

            conn.commit()
        return jsonify({'message': 'Heartbeat registered successfully.'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error.'}), 500

@app.route('/services', methods=['POST'])
def get_services():
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({'error': 'Invalid request payload.'}), 400

    token = data['token']

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT serviceId, token, lastNotification FROM services')
            services = cursor.fetchall()

            result = []
            for service in services:
                if verify_token(service['token'], token):
                    result.append({
                        'serviceId': service['serviceId'],
                        'lastNotification': service['lastNotification']
                    })

            return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)