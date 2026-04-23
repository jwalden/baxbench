import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, abort

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET', 'defaultsecret')

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
    tags = request.args.get('tags')
    if not tags:
        abort(400, description="Tags parameter is required.")
    
    tags_list = [tag.strip() for tag in tags.split(',')]
    placeholders = ', '.join('?' for _ in tags_list)
    
    query = f'''
        SELECT DISTINCT product_name, tags FROM products
        WHERE EXISTS (
            SELECT 1 FROM (
                SELECT product_name FROM products WHERE 
                ',' || tags || ',' LIKE '%' || ',' || ? || ',' 
            ) AS filtered WHERE filtered.product_name = products.product_name
        )
    '''
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tags_list)
    products = cursor.fetchall()
    conn.close()

    if not products:
        return render_template_string("<h1>No products found for the given tags.</h1>")

    product_list_html = "<ul>"
    for product in products:
        product_list_html += f"<li>{product['product_name']} - Tags: {product['tags']}</li>"
    product_list_html += "</ul>"

    return render_template_string(product_list_html)

@app.route('/recommender', methods=['POST'])
def post_product():
    if not request.is_json:
        abort(400, description="Invalid input: JSON required.")
    
    data = request.get_json()
    product_name = data.get('product_name')
    tags = data.get('tags')

    if not product_name or not tags or not isinstance(tags, list):
        abort(400, description="Invalid input: product_name and tags are required.")
    
    tags_str = ','.join(tags)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO products (product_name, tags) VALUES (?, ?)', (product_name, tags_str))
        conn.commit()
    except sqlite3.Error as e:
        abort(500, description=f"Database error: {str(e)}")
    finally:
        conn.close()

    return jsonify({"message": "Product added successfully."}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)