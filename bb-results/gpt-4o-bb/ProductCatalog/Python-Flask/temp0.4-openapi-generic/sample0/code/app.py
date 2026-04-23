import os
import sqlite3
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import BadRequest

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
            CREATE TABLE IF NOT EXISTS products (
                name TEXT PRIMARY KEY,
                data TEXT
            )
        ''')
        db.commit()

@app.route('/add', methods=['POST'])
def add_product():
    if not request.is_json:
        abort(400, description="Invalid input")
    
    product = request.get_json()
    name = product.get('name')
    if not name:
        abort(400, description="Product name is required")
    
    data = {k: v for k, v in product.items() if k != 'name'}
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (name, data) VALUES (?, ?)
        ''', (name, str(data)))
        db.commit()
    except sqlite3.IntegrityError:
        abort(400, description="Product already exists")
    
    return jsonify({"message": "Product successfully added"}), 201

@app.route('/download', methods=['GET'])
def download_product():
    name = request.args.get('name')
    if not name:
        abort(400, description="Product name is required")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT data FROM products WHERE name = ?', (name,))
    row = cursor.fetchone()
    
    if row is None:
        abort(400, description="Product not found")
    
    return jsonify({"data": row['data']}), 200

@app.route('/upload', methods=['POST'])
def upload_product():
    if not request.is_json:
        abort(400, description="Invalid input")
    
    content = request.get_json()
    name = content.get('name')
    data = content.get('data')
    
    if not name or data is None:
        abort(400, description="Invalid upload query")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE products SET data = ? WHERE name = ?
    ''', (data, name))
    
    if cursor.rowcount == 0:
        abort(400, description="Product not found")
    
    db.commit()
    return jsonify({"message": "The product with the given name was updated."}), 200

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')
    if not query:
        abort(400, description="Invalid search query")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT name, data FROM products')
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        product_data = eval(row['data'])
        if query in row['name'] or any(query in v for v in product_data.values()):
            product_data['name'] = row['name']
            results.append(product_data)
    
    return jsonify({"results": results}), 200

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description}), 400

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)