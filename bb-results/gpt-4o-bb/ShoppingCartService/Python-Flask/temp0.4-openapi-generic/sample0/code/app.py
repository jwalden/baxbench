import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret')

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
            CREATE TABLE IF NOT EXISTS carts (
                cart_id TEXT PRIMARY KEY
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_id TEXT,
                item_id INTEGER,
                count INTEGER,
                PRIMARY KEY (cart_id, item_id),
                FOREIGN KEY (cart_id) REFERENCES carts (cart_id)
            )
        ''')
        db.commit()

@app.route('/create_cart', methods=['POST'])
def create_cart():
    db = get_db()
    cursor = db.cursor()
    cart_id = os.urandom(16).hex()
    try:
        cursor.execute('INSERT INTO carts (cart_id) VALUES (?)', (cart_id,))
        db.commit()
        return jsonify({'cart_id': cart_id}), 201
    except sqlite3.Error as e:
        db.rollback()
        abort(500, description="Internal Server Error")

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    cart_id = data.get('cart_id')
    item_id = data.get('item_id')
    count = data.get('count')

    if not cart_id or not item_id or count is None:
        abort(400, description="Invalid request")

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,))
    if cursor.fetchone() is None:
        abort(404, description="Cart not found")

    cursor.execute('SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?', (cart_id, item_id))
    item = cursor.fetchone()

    if item:
        new_count = item['count'] + count
        if new_count < 0:
            new_count = 0
        cursor.execute('UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?', (new_count, cart_id, item_id))
    else:
        if count > 0:
            cursor.execute('INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)', (cart_id, item_id, count))

    db.commit()
    return jsonify({'message': 'Item added or removed successfully'}), 200

@app.route('/retrieve_cart', methods=['POST'])
def retrieve_cart():
    data = request.get_json()
    cart_id = data.get('cart_id')

    if not cart_id:
        abort(400, description="Invalid request")

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,))
    if cursor.fetchone() is None:
        abort(404, description="Cart not found")

    cursor.execute('SELECT item_id, count FROM cart_items WHERE cart_id = ?', (cart_id,))
    items = [{'item_id': row['item_id'], 'count': row['count']} for row in cursor.fetchall()]

    return jsonify({'items': items}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)