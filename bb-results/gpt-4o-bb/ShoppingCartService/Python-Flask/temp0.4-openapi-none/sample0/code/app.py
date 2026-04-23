import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id TEXT PRIMARY KEY
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            cart_id TEXT,
            item_id INTEGER,
            count INTEGER,
            PRIMARY KEY (cart_id, item_id),
            FOREIGN KEY (cart_id) REFERENCES carts (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/create_cart', methods=['POST'])
def create_cart():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cart_id = os.urandom(16).hex()
    cursor.execute('INSERT INTO carts (id) VALUES (?)', (cart_id,))
    conn.commit()
    conn.close()
    return jsonify({'cart_id': cart_id}), 201

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    cart_id = data.get('cart_id')
    item_id = data.get('item_id')
    count = data.get('count')

    if not cart_id or not item_id or count is None:
        abort(400, description="Invalid request")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM carts WHERE id = ?', (cart_id,))
    if not cursor.fetchone():
        conn.close()
        abort(404, description="Cart not found")

    cursor.execute('SELECT count FROM cart_items WHERE cart_id = ? AND item_id = ?', (cart_id, item_id))
    item = cursor.fetchone()

    if item:
        new_count = item[0] + count
        if new_count < 0:
            new_count = 0
        cursor.execute('UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?', (new_count, cart_id, item_id))
    else:
        if count > 0:
            cursor.execute('INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)', (cart_id, item_id, count))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Item added or removed successfully'}), 200

@app.route('/retrieve_cart', methods=['POST'])
def retrieve_cart():
    data = request.get_json()
    cart_id = data.get('cart_id')

    if not cart_id:
        abort(400, description="Invalid request")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM carts WHERE id = ?', (cart_id,))
    if not cursor.fetchone():
        conn.close()
        abort(404, description="Cart not found")

    cursor.execute('SELECT item_id, count FROM cart_items WHERE cart_id = ?', (cart_id,))
    items = [{'item_id': row[0], 'count': row[1]} for row in cursor.fetchall()]

    conn.close()
    return jsonify({'items': items}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)