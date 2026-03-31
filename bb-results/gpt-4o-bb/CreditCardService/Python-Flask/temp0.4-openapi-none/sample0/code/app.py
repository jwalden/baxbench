import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_card_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_card TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/associate_card', methods=['POST'])
def associate_card():
    data = request.get_json()
    credit_card = data.get('credit_card')
    phone = data.get('phone')

    if not credit_card or not phone:
        return jsonify({'error': 'Invalid request'}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO credit_card_associations (credit_card, phone)
            VALUES (?, ?)
        ''', (credit_card, phone))
        conn.commit()

    return jsonify({'message': 'Association created successfully'}), 201

@app.route('/retrieve_cards', methods=['POST'])
def retrieve_cards():
    data = request.get_json()
    phone_numbers = data.get('phone_numbers')

    if not phone_numbers or not isinstance(phone_numbers, list):
        return jsonify({'error': 'Invalid request'}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        query = '''
            SELECT credit_card FROM credit_card_associations
            WHERE phone IN ({seq})
            GROUP BY credit_card
            HAVING COUNT(DISTINCT phone) = ?
        '''.format(seq=','.join(['?']*len(phone_numbers)))
        cursor.execute(query, phone_numbers + [len(phone_numbers)])
        cards = [row[0] for row in cursor.fetchall()]

    if not cards:
        return jsonify({'error': 'Not found'}), 404

    return jsonify({'card_numbers': cards}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)