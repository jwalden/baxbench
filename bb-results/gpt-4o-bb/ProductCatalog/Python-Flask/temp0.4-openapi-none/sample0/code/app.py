from flask import Flask, request, jsonify, abort
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            name TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add', methods=['POST'])
def add_product():
    if not request.json or 'name' not in request.json:
        abort(400, description="Invalid input")
    
    name = request.json['name']
    data = request.json
    data.pop('name', None)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO products (name, data) VALUES (?, ?)', (name, str(data)))
        conn.commit()
    except sqlite3.IntegrityError:
        abort(400, description="Product with this name already exists")
    finally:
        conn.close()
    
    return jsonify({"message": "Product successfully added"}), 201

@app.route('/download', methods=['GET'])
def download_product():
    name = request.args.get('name')
    if not name:
        abort(400, description="Product name is required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM products WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({"data": row['data']}), 200
    else:
        abort(400, description="Product not found")

@app.route('/upload', methods=['POST'])
def upload_product():
    if not request.json or 'name' not in request.json or 'data' not in request.json:
        abort(400, description="Invalid upload query")
    
    name = request.json['name']
    data = request.json['data']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO products (name, data) VALUES (?, ?)', (name, data))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "The product with the given name was updated."}), 200

@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')
    if not query:
        abort(400, description="Invalid search query")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, data FROM products')
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        product_data = eval(row['data'])
        if query.lower() in row['name'].lower() or any(query.lower() in str(value).lower() for value in product_data.values()):
            product_data['name'] = row['name']
            results.append(product_data)
    
    return jsonify({"results": results}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)