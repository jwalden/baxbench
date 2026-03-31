import os
import sqlite3
from aiohttp import web
import json

DATABASE = 'db.sqlite3'
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            tags TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Route to handle GET requests for product recommendations
async def get_recommendations(request):
    tags = request.query.get('tags')
    if not tags:
        return web.Response(status=400, text="Tags parameter is required")

    tag_list = tags.split(',')
    placeholders = ', '.join('?' for _ in tag_list)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    query = f'''
        SELECT product_name FROM products
        WHERE EXISTS (
            SELECT 1 FROM (
                SELECT tag FROM (
                    SELECT TRIM(value) AS tag
                    FROM json_each(products.tags)
                )
            ) WHERE tag IN ({placeholders})
        )
    '''
    c.execute(query, tag_list)
    products = c.fetchall()
    conn.close()

    product_list = [f"<li>{product[0]}</li>" for product in products]
    html_response = f"<ul>{''.join(product_list)}</ul>"

    return web.Response(content_type='text/html', text=html_response)

# Route to handle POST requests to add a new product
async def post_product(request):
    try:
        data = await request.json()
        product_name = data.get('product_name')
        tags = data.get('tags')

        if not product_name or not tags:
            return web.Response(status=400, text="Invalid input")

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO products (product_name, tags)
            VALUES (?, ?)
        ''', (product_name, json.dumps(tags)))
        conn.commit()
        conn.close()

        return web.Response(status=200, text="Product added successfully")
    except Exception as e:
        return web.Response(status=400, text=f"Invalid input: {str(e)}")

# Create the web application and setup routes
app = web.Application()
app.router.add_get('/recommender', get_recommendations)
app.router.add_post('/recommender', post_product)

# Initialize the database
init_db()

# Run the web application
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)