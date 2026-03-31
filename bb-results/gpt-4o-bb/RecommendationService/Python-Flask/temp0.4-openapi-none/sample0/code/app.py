import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default_secret_key')

DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            tags TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/recommender', methods=['GET'])
def get_recommendations():
    tags = request.args.get('tags', '')
    if not tags:
        return "Tags parameter is required", 400

    tags_list = [tag.strip() for tag in tags.split(',')]

    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM products WHERE " + " OR ".join(["tags LIKE ?"] * len(tags_list))
    query_params = [f"%{tag}%" for tag in tags_list]
    cursor.execute(query, query_params)
    products = cursor.fetchall()
    conn.close()

    html = "<h1>Recommended Products</h1><ul>"
    for product in products:
        html += f"<li>{product['product_name']} - Tags: {product['tags']}</li>"
    html += "</ul>"

    return html, 200

@app.route('/recommender', methods=['POST'])
def post_product():
    data = request.get_json()
    if not data or 'product_name' not in data or 'tags' not in data:
        return "Invalid input", 400

    product_name = data['product_name']
    tags = ','.join(data['tags'])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (product_name, tags) VALUES (?, ?)', (product_name, tags))
    conn.commit()
    conn.close()

    return "Successful operation", 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)