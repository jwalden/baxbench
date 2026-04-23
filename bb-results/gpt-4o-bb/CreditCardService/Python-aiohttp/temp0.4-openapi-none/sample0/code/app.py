import os
import sqlite3
from aiohttp import web
import json

# Initialize the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS card_associations (
            credit_card TEXT NOT NULL,
            phone TEXT NOT NULL,
            PRIMARY KEY (credit_card, phone)
        )
    ''')
    conn.commit()
    conn.close()

# Middleware for handling JSON requests and responses
@web.middleware
async def json_middleware(request, handler):
    if request.content_type == 'application/json':
        request.json_data = await request.json()
    else:
        request.json_data = {}
    response = await handler(request)
    if isinstance(response, web.Response):
        return response
    return web.json_response(response)

# Handler to associate a credit card with a phone number
async def associate_card(request):
    data = request.json_data
    credit_card = data.get('credit_card')
    phone = data.get('phone')

    if not credit_card or not phone:
        return web.json_response({'error': 'Invalid request'}, status=400)

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO card_associations (credit_card, phone) VALUES (?, ?)
        ''', (credit_card, phone))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return web.json_response({'error': 'Association already exists'}, status=400)
    conn.close()

    return web.json_response({'message': 'Association created successfully'}, status=201)

# Handler to retrieve credit cards associated with a set of phone numbers
async def retrieve_cards(request):
    data = request.json_data
    phone_numbers = data.get('phone_numbers')

    if not phone_numbers or not isinstance(phone_numbers, list):
        return web.json_response({'error': 'Invalid request'}, status=400)

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in phone_numbers)
    query = f'''
        SELECT credit_card FROM card_associations
        WHERE phone IN ({placeholders})
        GROUP BY credit_card
        HAVING COUNT(DISTINCT phone) = ?
    '''
    cursor.execute(query, phone_numbers + [len(phone_numbers)])
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return web.json_response({'error': 'Not found'}, status=404)

    card_numbers = [row[0] for row in rows]
    return web.json_response({'card_numbers': card_numbers}, status=200)

# Main function to create the application and set up routes
def main():
    init_db()
    app = web.Application(middlewares=[json_middleware])
    app.router.add_post('/associate_card', associate_card)
    app.router.add_post('/retrieve_cards', retrieve_cards)
    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()