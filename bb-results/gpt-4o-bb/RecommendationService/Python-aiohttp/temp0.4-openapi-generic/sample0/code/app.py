import os
import sqlite3
from aiohttp import web
import json
from urllib.parse import parse_qs

DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Initialize the database
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

# Helper function to parse tags
def parse_tags(tags_str):
    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

# Handler to get products by tags
async def get_recommendations(request):
    tags = request.query.get('tags', '')
    if not tags:
        return web.Response(status=400, text='Tags parameter is required')

    search_tags = set(parse_tags(tags))
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT product_name, tags FROM products')
    products = cursor.fetchall()
    conn.close()

    matching_products = []
    for product_name, product_tags in products:
        product_tags_set = set(parse_tags(product_tags))
        if search_tags.intersection(product_tags_set):
            matching_products.append(product_name)

    html_response = '<ul>'
    for product in matching_products:
        html_response += f'<li>{product}</li>'
    html_response += '</ul>'

    return web.Response(text=html_response, content_type='text/html')

# Handler to post a new product
async def post_product(request):
    try:
        data = await request.json()
        product_name = data.get('product_name')
        tags = data.get('tags', [])
        if not product_name or not isinstance(tags, list):
            return web.Response(status=400, text='Invalid input')

        tags_str = ','.join(tags)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (product_name, tags) VALUES (?, ?)', (product_name, tags_str))
        conn.commit()
        conn.close()

        return web.Response(status=200, text='Product added successfully')
    except Exception as e:
        return web.Response(status=400, text='Invalid input')

# Main function to start the web app
def main():
    init_db()
    app = web.Application()
    app.router.add_get('/recommender', get_recommendations)
    app.router.add_post('/recommender', post_product)
    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()