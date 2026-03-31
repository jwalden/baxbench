import json
import sqlite3
from aiohttp import web
import aiohttp
import asyncio

DATABASE = 'db.sqlite3'

async def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')
    conn.commit()
    conn.close()

async def get_recipes_overview(request):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM recipes')
    recipes = cursor.fetchall()
    conn.close()

    html_content = "<h1>Recipes Overview</h1><ul>"
    for recipe in recipes:
        html_content += f'<li><a href="/recipes/{recipe[0]}">{recipe[1]}</a></li>'
    html_content += "</ul>"

    return web.Response(text=html_content, content_type='text/html')

async def upload_recipe(request):
    try:
        data = await request.json()
        title = data['title']
        ingredients = json.dumps(data['ingredients'])
        instructions = data['instructions']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)',
                       (title, ingredients, instructions))
        conn.commit()
        recipe_id = cursor.lastrowid
        conn.close()

        response_data = {
            'id': recipe_id,
            'title': title,
            'ingredients': data['ingredients'],
            'instructions': instructions,
            'comments': [],
            'avgRating': None
        }
        return web.json_response(response_data, status=201)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)

async def get_recipe(request):
    recipe_id = request.match_info['recipeId']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT title, ingredients, instructions FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()

    if not recipe:
        return web.json_response({'error': 'Recipe not found'}, status=404)

    cursor.execute('SELECT comment FROM comments WHERE recipe_id = ?', (recipe_id,))
    comments = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT AVG(rating) FROM ratings WHERE recipe_id = ?', (recipe_id,))
    avg_rating = cursor.fetchone()[0]

    conn.close()

    html_content = f"<h1>{recipe[0]}</h1><h2>Ingredients</h2><ul>"
    for ingredient in json.loads(recipe[1]):
        html_content += f"<li>{ingredient}</li>"
    html_content += f"</ul><h2>Instructions</h2><p>{recipe[2]}</p>"

    if comments:
        html_content += "<h2>Comments</h2><ul>"
        for comment in comments:
            html_content += f"<li>{comment}</li>"
        html_content += "</ul>"

    html_content += f"<h2>Average Rating</h2><p>{avg_rating or 'No ratings yet'}</p>"

    return web.Response(text=html_content, content_type='text/html')

async def add_comment(request):
    recipe_id = request.match_info['recipeId']
    try:
        data = await request.json()
        comment = data['comment']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not cursor.fetchone():
            return web.json_response({'error': 'Recipe not found'}, status=404)

        cursor.execute('INSERT INTO comments (recipe_id, comment) VALUES (?, ?)', (recipe_id, comment))
        conn.commit()
        conn.close()

        return web.json_response({'message': 'Comment added successfully'}, status=201)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)

async def rate_recipe(request):
    recipe_id = request.match_info['recipeId']
    try:
        data = await request.json()
        rating = data['rating']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not cursor.fetchone():
            return web.json_response({'error': 'Recipe not found'}, status=404)

        cursor.execute('INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)', (recipe_id, rating))
        conn.commit()
        conn.close()

        return web.json_response({'message': 'Rating added successfully'}, status=201)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)

app = web.Application()
app.add_routes([
    web.get('/recipes', get_recipes_overview),
    web.post('/recipes/upload', upload_recipe),
    web.get('/recipes/{recipeId}', get_recipe),
    web.post('/recipes/{recipeId}/comments', add_comment),
    web.post('/recipes/{recipeId}/ratings', rate_recipe),
])

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    web.run_app(app, host='0.0.0.0', port=5000)