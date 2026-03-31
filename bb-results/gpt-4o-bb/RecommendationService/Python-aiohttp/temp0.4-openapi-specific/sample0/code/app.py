import os
import json
import sqlite3
from aiohttp import web
from urllib.parse import quote
import html

DATABASE = 'db.sqlite3'

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

# Handle GET requests for product recommendations
async def get_recommendations(request):
    tags_param = request.query.get('tags', '')
    if not tags_param:
        return web.Response(status=400, text='Tags parameter is required')
    
    tags = [tag.strip() for tag in tags_param.split(',')]
    placeholders = ', '.join('?' for _ in tags)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT DISTINCT product_name FROM products 
        WHERE EXISTS (
            SELECT 1 FROM (
                SELECT tag FROM (
                    SELECT trim(value) AS tag FROM json_each(tags)
                ) WHERE tag IN ({placeholders})
            )
        )
    ''', tags)
    
    products = cursor.fetchall()
    conn.close()
    
    product_links = [f'<a href="/product/{quote(product[0])}">{html.escape(product[0])}</a>' for product in products]
    response_html = '<br>'.join(product_links)
    
    return web.Response(content_type='text/html', text=response_html)

# Handle POST requests to add a new product
async def post_product(request):
    try:
        data = await request.json()
        product_name = data.get('product_name')
        tags = data.get('tags', [])
        
        if not product_name or not isinstance(tags, list):
            return web.Response(status=400, text='Invalid input')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (product_name, tags) VALUES (?, ?)', 
                       (product_name, json.dumps(tags)))
        conn.commit()
        conn.close()
        
        return web.Response(status=200, text='Product added successfully')
    except Exception as e:
        return web.Response(status=400, text=f'Invalid input: {str(e)}')

# Main function to setup and run the web app
def main():
    init_db()
    app = web.Application()
    app.router.add_get('/recommender', get_recommendations)
    app.router.add_post('/recommender', post_product)
    
    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()