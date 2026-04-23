import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/click', methods=['POST'])
def register_click():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clicks (timestamp) VALUES (CURRENT_TIMESTAMP)')
        conn.commit()
        conn.close()
        return jsonify({'message': 'Click registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/clicks', methods=['GET'])
def retrieve_clicks():
    date = request.args.get('date')
    direction = request.args.get('direction')

    if not date or not direction or direction not in ['<', '>', '<=', '>=']:
        return jsonify({'error': 'Invalid request'}), 400

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        query = f'SELECT id, timestamp FROM clicks WHERE timestamp {direction} ?'
        cursor.execute(query, (date,))
        clicks = cursor.fetchall()
        conn.close()

        if not clicks:
            return jsonify({'error': 'No clicks found'}), 404

        result = [{'id': str(click[0]), 'timestamp': click[1]} for click in clicks]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)