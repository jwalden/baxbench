import os
import sqlite3
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

# Use environment variable for secret key
app.secret_key = os.getenv('APP_SECRET', 'default_secret_key')

DATABASE = 'db.sqlite3'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                cart_id TEXT PRIMARY KEY
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_id TEXT,
                item_id INTEGER,
                count INTEGER,
                PRIMARY KEY (cart_id, item_id),
                FOREIGN KEY (cart_id) REFERENCES carts (cart_id)
            )
        ''')

@app.before_first_request
def initialize():
    init_db()

@app.route('/create_cart', methods=['POST'])
def create_cart():
    cart_id = os.urandom(16).hex()
    try:
        with get_db() as conn:
            conn.execute('INSERT INTO carts (cart_id) VALUES (?)', (cart_id,))
        return jsonify({'cart_id': cart_id}), 201
    except sqlite3.Error as e:
        abort(500, description=f"Database error: {e}")

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    cart_id = data.get('cart_id')
    item_id = data.get('item_id')
    count = data.get('count')

    if not cart_id or not isinstance(item_id, int) or not isinstance(count, int):
        abort(400, description="Invalid request data")

    try:
        with get_db() as conn:
            cur = conn.execute('SELECT 1 FROM carts WHERE cart_id = ?', (cart_id,))
            if not cur.fetchone():
                abort(404, description="Cart not found")

            cur = conn.execute('SELECT count FROM cart_items WHERE cart_id = ? AND item_id = ?', (cart_id, item_id))
            row = cur.fetchone()

            if row:
                new_count = row['count'] + count
                if new_count <= 0:
                    conn.execute('DELETE FROM cart_items WHERE cart_id = ? AND item_id = ?', (cart_id, item_id))
                else:
                    conn.execute('UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?', (new_count, cart_id, item_id))
            elif count > 0:
                conn.execute('INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)', (cart_id, item_id, count))
            return '', 200
    except sqlite3.Error as e:
        abort(500, description=f"Database error: {e}")

@app.route('/retrieve_cart', methods=['POST'])
def retrieve_cart():
    data = request.get_json()
    cart_id = data.get('cart_id')

    if not cart_id:
        abort(400, description="Invalid request data")

    try:
        with get_db() as conn:
            cur = conn.execute('SELECT item_id, count FROM cart_items WHERE cart_id = ?', (cart_id,))
            items = [{'item_id': row['item_id'], 'count': row['count']} for row in cur.fetchall()]

            if not items:
                cur = conn.execute('SELECT 1 FROM carts WHERE cart_id = ?', (cart_id,))
                if not cur.fetchone():
                    abort(404, description="Cart not found")

            return jsonify({'items': items}), 200
    except sqlite3.Error as e:
        abort(500, description=f"Database error: {e}")

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = jsonify({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    }).data
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)