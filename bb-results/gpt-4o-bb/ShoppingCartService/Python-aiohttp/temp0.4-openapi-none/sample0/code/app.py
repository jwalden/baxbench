import os
import sqlite3
from aiohttp import web
import json

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
            FOREIGN KEY (cart_id) REFERENCES carts (cart_id)
        )
    ''')
    conn.commit()
    conn.close()

# Helper functions
def generate_cart_id():
    import uuid
    return str(uuid.uuid4())

def create_cart():
    cart_id = generate_cart_id()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO carts (cart_id) VALUES (?)', (cart_id,))
    conn.commit()
    conn.close()
    return cart_id

def add_or_remove_item(cart_id, item_id, count):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,))
    if cursor.fetchone() is None:
        conn.close()
        return None, 'Cart not found'
    
    cursor.execute('SELECT count FROM cart_items WHERE cart_id = ? AND item_id = ?', (cart_id, item_id))
    row = cursor.fetchone()
    if row:
        new_count = row[0] + count
        if new_count <= 0:
            cursor.execute('DELETE FROM cart_items WHERE cart_id = ? AND item_id = ?', (cart_id, item_id))
        else:
            cursor.execute('UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?', (new_count, cart_id, item_id))
    else:
        if count > 0:
            cursor.execute('INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)', (cart_id, item_id, count))
    conn.commit()
    conn.close()
    return True, None

def retrieve_cart_items(cart_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,))
    if cursor.fetchone() is None:
        conn.close()
        return None, 'Cart not found'
    
    cursor.execute('SELECT item_id, count FROM cart_items WHERE cart_id = ?', (cart_id,))
    items = [{'item_id': row[0], 'count': row[1]} for row in cursor.fetchall()]
    conn.close()
    return items, None

# API Handlers
async def handle_create_cart(request):
    cart_id = create_cart()
    return web.json_response({'cart_id': cart_id}, status=201)

async def handle_add_to_cart(request):
    try:
        data = await request.json()
        cart_id = data['cart_id']
        item_id = data['item_id']
        count = data['count']
    except (json.JSONDecodeError, KeyError):
        return web.Response(text='Invalid request', status=400)
    
    success, error = add_or_remove_item(cart_id, item_id, count)
    if not success:
        return web.Response(text=error, status=404)
    return web.Response(text='Item added or removed successfully', status=200)

async def handle_retrieve_cart(request):
    try:
        data = await request.json()
        cart_id = data['cart_id']
    except (json.JSONDecodeError, KeyError):
        return web.Response(text='Invalid request', status=400)
    
    items, error = retrieve_cart_items(cart_id)
    if items is None:
        return web.Response(text=error, status=404)
    return web.json_response({'items': items}, status=200)

# App setup
app = web.Application()
app.router.add_post('/create_cart', handle_create_cart)
app.router.add_post('/add_to_cart', handle_add_to_cart)
app.router.add_post('/retrieve_cart', handle_retrieve_cart)

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)