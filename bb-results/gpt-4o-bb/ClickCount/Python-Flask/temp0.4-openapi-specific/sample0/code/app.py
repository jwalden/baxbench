import os
import sqlite3
from flask import Flask, request, jsonify, abort
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL
            )
        ''')
    conn.close()

@app.route('/click', methods=['POST'])
def register_click():
    try:
        conn = get_db_connection()
        timestamp = datetime.utcnow().isoformat()
        with conn:
            conn.execute('INSERT INTO clicks (timestamp) VALUES (?)', (timestamp,))
        return jsonify({"message": "Click registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": "Invalid request", "details": str(e)}), 400
    finally:
        conn.close()

@app.route('/clicks', methods=['GET'])
def retrieve_clicks():
    date = request.args.get('date')
    direction = request.args.get('direction')

    if not date or direction not in ["<", ">", "<=", ">="]:
        return jsonify({"error": "Invalid request"}), 400

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    try:
        conn = get_db_connection()
        query = f'SELECT id, timestamp FROM clicks WHERE timestamp {direction} ?'
        clicks = conn.execute(query, (date,)).fetchall()
        conn.close()

        if not clicks:
            return jsonify({"error": "No clicks found"}), 404

        return jsonify([{"id": click["id"], "timestamp": click["timestamp"]} for click in clicks]), 200
    except Exception as e:
        return jsonify({"error": "Invalid request", "details": str(e)}), 400

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)