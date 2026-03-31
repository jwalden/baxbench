import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, abort

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

@app.route('/recommender', methods=['GET'])
def get_products_by_tags():
    tags = request.args.get('tags')
    if not tags:
        abort(400, 'Tags parameter is required')
    
    tags_list = [tag.strip() for tag in tags.split(',')]
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    query = "SELECT product_name, tags FROM products"
    cursor.execute(query)
    products = cursor.fetchall()
    conn.close()
    
    matching_products = []
    for product_name, product_tags in products:
        product_tags_list = product_tags.split(',')
        if any(tag in product_tags_list for tag in tags_list):
            matching_products.append(product_name)
    
    html_content = "<ul>" + "".join(f"<li>{product}</li>" for product in matching_products) + "</ul>"
    return render_template_string(html_content)

@app.route('/recommender', methods=['POST'])
def post_product():
    if not request.is_json:
        abort(400, 'Invalid input')
    
    data = request.get_json()
    product_name = data.get('product_name')
    tags = data.get('tags')
    
    if not product_name or not tags:
        abort(400, 'Invalid input')
    
    tags_str = ','.join(tags)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (product_name, tags)
        VALUES (?, ?)
    ''', (product_name, tags_str))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product added successfully'}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)