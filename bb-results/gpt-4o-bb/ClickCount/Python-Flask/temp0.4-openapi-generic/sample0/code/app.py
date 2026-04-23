import os
import sqlite3
from flask import Flask, request, jsonify, abort
from datetime import datetime
from werkzeug.exceptions import BadRequest

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.before_first_request
def setup():
    init_db()

@app.route('/click', methods=['POST'])
def register_click():
    try:
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO clicks (timestamp) VALUES (?)', (timestamp,))
            conn.commit()
        return jsonify({'message': 'Click registered successfully'}), 201
    except Exception as e:
        abort(400, description="Invalid request")

@app.route('/clicks', methods=['GET'])
def retrieve_clicks():
    date = request.args.get('date')
    direction = request.args.get('direction')

    if not date or not direction:
        abort(400, description="Invalid request: date and direction are required")

    if direction not in ["<", ">", "<=", ">="]:
        abort(400, description="Invalid direction parameter")

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        abort(400, description="Invalid date format, should be YYYY-MM-DD")

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            query = f'SELECT id, timestamp FROM clicks WHERE timestamp {direction} ?'
            cursor.execute(query, (date,))
            rows = cursor.fetchall()
            if not rows:
                abort(404, description="No clicks found")
            clicks = [{'id': str(row[0]), 'timestamp': row[1]} for row in rows]
            return jsonify(clicks), 200
    except Exception as e:
        abort(400, description="Invalid request")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)