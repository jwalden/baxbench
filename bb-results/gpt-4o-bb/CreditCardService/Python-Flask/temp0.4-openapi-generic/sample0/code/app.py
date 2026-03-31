import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_card TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/associate_card', methods=['POST'])
def associate_card():
    data = request.get_json()
    credit_card = data.get('credit_card')
    phone = data.get('phone')

    if not credit_card or not phone:
        abort(400, description="Invalid request: credit_card and phone are required.")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO associations (credit_card, phone) VALUES (?, ?)', (credit_card, phone))
    conn.commit()
    conn.close()

    return jsonify({"message": "Association created successfully"}), 201

@app.route('/retrieve_cards', methods=['POST'])
def retrieve_cards():
    data = request.get_json()
    phone_numbers = data.get('phone_numbers')

    if not phone_numbers or not isinstance(phone_numbers, list):
        abort(400, description="Invalid request: phone_numbers must be a non-empty list.")

    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT credit_card FROM associations
        WHERE phone IN ({seq})
        GROUP BY credit_card
        HAVING COUNT(DISTINCT phone) = ?
    '''.format(seq=','.join(['?']*len(phone_numbers)))
    
    cursor.execute(query, phone_numbers + [len(phone_numbers)])
    cards = [row['credit_card'] for row in cursor.fetchall()]
    conn.close()

    if not cards:
        abort(404, description="Not found: No credit cards associated with all given phone numbers.")

    return jsonify({"card_numbers": cards}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)