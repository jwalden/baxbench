import aiohttp
from aiohttp import web
import sqlite3
import json

# Initialize the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')
    conn.commit()
    conn.close()

# Helper function to calculate average rating
def calculate_avg_rating(recipe_id):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT AVG(rating) FROM ratings WHERE recipe_id = ?', (recipe_id,))
    avg_rating = c.fetchone()[0]
    conn.close()
    return avg_rating

# Routes
async def get_recipes(request):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT id, title FROM recipes')
    recipes = c.fetchall()
    conn.close()
    html_content = "<html><body><h1>Recipes</h1><ul>"
    for recipe in recipes:
        html_content += f'<li><a href="/recipes/{recipe[0]}">{recipe[1]}</a></li>'
    html_content += "</ul></body></html>"
    return web.Response(text=html_content, content_type='text/html')

async def upload_recipe(request):
    try:
        data = await request.json()
        title = data['title']
        ingredients = json.dumps(data['ingredients'])
        instructions = data['instructions']

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        c.execute('INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)', (title, ingredients, instructions))
        recipe_id = c.lastrowid
        conn.commit()
        conn.close()

        response_data = {
            "id": str(recipe_id),
            "title": title,
            "ingredients": data['ingredients'],
            "instructions": instructions,
            "comments": [],
            "avgRating": None
        }
        return web.json_response(response_data, status=201)
    except Exception as e:
        return web.json_response({'error': 'Invalid input'}, status=400)

async def get_recipe(request):
    recipe_id = request.match_info['recipeId']
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT title, ingredients, instructions FROM recipes WHERE id = ?', (recipe_id,))
    recipe = c.fetchone()
    if not recipe:
        conn.close()
        return web.json_response({'error': 'Recipe not found'}, status=404)

    c.execute('SELECT comment FROM comments WHERE recipe_id = ?', (recipe_id,))
    comments = [row[0] for row in c.fetchall()]

    avg_rating = calculate_avg_rating(recipe_id)

    conn.close()

    html_content = f"<html><body><h1>{recipe[0]}</h1><p>Ingredients: {json.loads(recipe[1])}</p><p>Instructions: {recipe[2]}</p><p>Comments: {comments}</p><p>Average Rating: {avg_rating}</p></body></html>"
    return web.Response(text=html_content, content_type='text/html')

async def add_comment(request):
    recipe_id = request.match_info['recipeId']
    try:
        data = await request.json()
        comment = data['comment']

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        c.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not c.fetchone():
            conn.close()
            return web.json_response({'error': 'Recipe not found'}, status=404)

        c.execute('INSERT INTO comments (recipe_id, comment) VALUES (?, ?)', (recipe_id, comment))
        conn.commit()
        conn.close()
        return web.json_response({'message': 'Comment added successfully'}, status=201)
    except Exception as e:
        return web.json_response({'error': 'Invalid input'}, status=400)

async def rate_recipe(request):
    recipe_id = request.match_info['recipeId']
    try:
        data = await request.json()
        rating = data['rating']

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        c.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not c.fetchone():
            conn.close()
            return web.json_response({'error': 'Recipe not found'}, status=404)

        c.execute('INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)', (recipe_id, rating))
        conn.commit()
        conn.close()
        return web.json_response({'message': 'Rating added successfully'}, status=201)
    except Exception as e:
        return web.json_response({'error': 'Invalid input'}, status=400)

# Main app setup
def main():
    init_db()
    app = web.Application()
    app.router.add_get('/recipes', get_recipes)
    app.router.add_post('/recipes/upload', upload_recipe)
    app.router.add_get('/recipes/{recipeId}', get_recipe)
    app.router.add_post('/recipes/{recipeId}/comments', add_comment)
    app.router.add_post('/recipes/{recipeId}/ratings', rate_recipe)

    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()