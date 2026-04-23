import os
import json
import uuid
import sqlite3
from aiohttp import web
from aiohttp.web import Response
from passlib.context import CryptContext

# Initialize database
DATABASE = 'db.sqlite3'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS carts (
    cart_id TEXT PRIMARY KEY
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS cart_items (
    cart_id TEXT,
    item_id INTEGER,
    count INTEGER,
    PRIMARY KEY (cart_id, item_id),
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
)
''')
conn.commit()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper functions
def get_cart(cart_id):
    cursor.execute("SELECT item_id, count FROM cart_items WHERE cart_id = ?", (cart_id,))
    return cursor.fetchall()

def create_cart():
    cart_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO carts (cart_id) VALUES (?)", (cart_id,))
    conn.commit()
    return cart_id

def add_to_cart(cart_id, item_id, count):
    cursor.execute("SELECT 1 FROM carts WHERE cart_id = ?", (cart_id,))
    if not cursor.fetchone():
        return None

    cursor.execute("SELECT count FROM cart_items WHERE cart_id = ? AND item_id = ?", (cart_id, item_id))
    row = cursor.fetchone()
    if row:
        new_count = row[0] + count
        if new_count <= 0:
            cursor.execute("DELETE FROM cart_items WHERE cart_id = ? AND item_id = ?", (cart_id, item_id))
        else:
            cursor.execute("UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?", (new_count, cart_id, item_id))
    else:
        if count > 0:
            cursor.execute("INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)", (cart_id, item_id, count))
    conn.commit()
    return True

# Routes
async def handle_create_cart(request):
    cart_id = create_cart()
    return web.json_response({'cart_id': cart_id}, status=201)

async def handle_add_to_cart(request):
    try:
        data = await request.json()
        cart_id = data['cart_id']
        item_id = data['item_id']
        count = data['count']
    except (KeyError, json.JSONDecodeError):
        return web.json_response({'error': 'Invalid request'}, status=400)

    if not isinstance(cart_id, str) or not isinstance(item_id, int) or not isinstance(count, int):
        return web.json_response({'error': 'Invalid data types'}, status=400)

    result = add_to_cart(cart_id, item_id, count)
    if result is None:
        return web.json_response({'error': 'Cart not found'}, status=404)
    return web.json_response({'message': 'Item added or removed successfully'}, status=200)

async def handle_retrieve_cart(request):
    try:
        data = await request.json()
        cart_id = data['cart_id']
    except (KeyError, json.JSONDecodeError):
        return web.json_response({'error': 'Invalid request'}, status=400)

    if not isinstance(cart_id, str):
        return web.json_response({'error': 'Invalid data types'}, status=400)

    items = get_cart(cart_id)
    if not items:
        return web.json_response({'error': 'Cart not found'}, status=404)
    return web.json_response({'items': [{'item_id': item_id, 'count': count} for item_id, count in items]}, status=200)

# Application setup
app = web.Application()
app.add_routes([
    web.post('/create_cart', handle_create_cart),
    web.post('/add_to_cart', handle_add_to_cart),
    web.post('/retrieve_cart', handle_retrieve_cart)
])

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)