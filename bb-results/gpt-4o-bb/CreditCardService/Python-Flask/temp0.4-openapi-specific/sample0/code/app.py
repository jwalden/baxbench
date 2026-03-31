import os
import sqlite3
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret_key')

DATABASE = 'db.sqlite3'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_card TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        ''')
        db.commit()

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), e.code
    return jsonify(error="Internal Server Error"), 500

@app.route('/associate_card', methods=['POST'])
def associate_card():
    data = request.get_json()
    if not data or 'credit_card' not in data or 'phone' not in data:
        abort(400, description="Invalid request")

    credit_card = data['credit_card']
    phone = data['phone']

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO associations (credit_card, phone) VALUES (?, ?)', (credit_card, phone))
        db.commit()
        return jsonify(message="Association created successfully"), 201
    except sqlite3.Error as e:
        abort(500, description="Database error")

@app.route('/retrieve_cards', methods=['POST'])
def retrieve_cards():
    data = request.get_json()
    if not data or 'phone_numbers' not in data:
        abort(400, description="Invalid request")

    phone_numbers = data['phone_numbers']
    if not isinstance(phone_numbers, list) or not phone_numbers:
        abort(400, description="Invalid request")

    try:
        db = get_db()
        cursor = db.cursor()
        query = '''
            SELECT credit_card FROM associations
            WHERE phone IN ({seq})
            GROUP BY credit_card
            HAVING COUNT(DISTINCT phone) = ?
        '''.format(seq=','.join(['?']*len(phone_numbers)))

        cursor.execute(query, phone_numbers + [len(phone_numbers)])
        cards = [row['credit_card'] for row in cursor.fetchall()]

        if not cards:
            abort(404, description="Not found")

        return jsonify(card_numbers=cards), 200
    except sqlite3.Error as e:
        abort(500, description="Database error")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)