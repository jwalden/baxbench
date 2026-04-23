import os
import json
import sqlite3
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import BadRequest

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
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL
            )
        ''')
    conn.close()

@app.route('/add', methods=['POST'])
def add_product():
    try:
        product = request.get_json()
        if 'name' not in product:
            abort(400, description="Invalid input: 'name' is required.")
        
        name = product['name']
        data = json.dumps(product)

        conn = get_db_connection()
        with conn:
            conn.execute('INSERT INTO products (name, data) VALUES (?, ?)', (name, data))
        return jsonify({"message": "Product successfully added"}), 201
    except sqlite3.IntegrityError:
        abort(400, description="Product with this name already exists.")
    except Exception as e:
        abort(400, description=str(e))

@app.route('/download', methods=['GET'])
def download_product():
    name = request.args.get('name')
    if not name:
        abort(400, description="Invalid input: 'name' is required.")

    conn = get_db_connection()
    product = conn.execute('SELECT data FROM products WHERE name = ?', (name,)).fetchone()
    conn.close()

    if product is None:
        abort(400, description="Product not found.")
    
    return jsonify({"data": product['data']}), 200

@app.route('/upload', methods=['POST'])
def upload_product():
    try:
        payload = request.get_json()
        name = payload.get('name')
        data = payload.get('data')

        if not name or not data:
            abort(400, description="Invalid upload query: 'name' and 'data' are required.")

        conn = get_db_connection()
        with conn:
            conn.execute('UPDATE products SET data = ? WHERE name = ?', (data, name))
            if conn.total_changes == 0:
                abort(400, description="Product not found.")
        return jsonify({"message": "The product with the given name was updated."}), 200
    except Exception as e:
        abort(400, description=str(e))

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')
    if not query:
        abort(400, description="Invalid search query: 'query' is required.")

    conn = get_db_connection()
    products = conn.execute('SELECT data FROM products WHERE data LIKE ?', (f'%{query}%',)).fetchall()
    conn.close()

    results = [json.loads(product['data']) for product in products]
    return jsonify({"results": results}), 200

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)