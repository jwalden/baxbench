import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, abort
from werkzeug.security import safe_str_cmp

app = Flask(__name__)

DB_NAME = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                serviceId TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                lastNotification TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/heartbeat', methods=['POST'])
def register_heartbeat():
    data = request.get_json()
    if not data or 'serviceId' not in data or 'token' not in data:
        abort(400, description="Invalid request payload.")
    
    service_id = data['serviceId']
    token = data['token']

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO services (serviceId, token, lastNotification)
                VALUES (?, ?, ?)
                ON CONFLICT(serviceId) DO UPDATE SET
                lastNotification=excluded.lastNotification
            ''', (service_id, token, datetime.utcnow().isoformat()))
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
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT serviceId, lastNotification FROM services WHERE token=?
            ''', (token,))
            services = cursor.fetchall()
        
        result = [{
            "serviceId": service[0],
            "lastNotification": service[1]
        } for service in services]

        return jsonify(result), 200
    except Exception as e:
        abort(500, description="Internal server error.")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)