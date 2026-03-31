import sqlite3
from aiohttp import web
import json
import html

DATABASE = 'db.sqlite3'

# Initialize the SQLite database
def init_db():
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

# Helper function to calculate average rating
def calculate_avg_rating(recipe_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT AVG(rating) FROM ratings WHERE recipe_id = ?', (recipe_id,))
    avg_rating = cursor.fetchone()[0]
    conn.close()
    return avg_rating

# Helper function to get recipe comments
def get_comments(recipe_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT comment FROM comments WHERE recipe_id = ?', (recipe_id,))
    comments = [row[0] for row in cursor.fetchall()]
    conn.close()
    return comments

# Route to get an overview of recipes
async def get_recipes(request):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM recipes')
    recipes = cursor.fetchall()
    conn.close()

    html_content = '<h1>Recipes Overview</h1><ul>'
    for recipe_id, title in recipes:
        html_content += f'<li><a href="/recipes/{recipe_id}">{html.escape(title)}</a></li>'
    html_content += '</ul>'
    return web.Response(text=html_content, content_type='text/html')

# Route to upload a new recipe
async def upload_recipe(request):
    try:
        data = await request.json()
        title = data.get('title')
        ingredients = data.get('ingredients')
        instructions = data.get('instructions')

        if not title or not ingredients or not instructions:
            raise ValueError("Invalid input")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)',
                       (title, json.dumps(ingredients), instructions))
        conn.commit()
        recipe_id = cursor.lastrowid
        conn.close()

        response_data = {
            "id": str(recipe_id),
            "title": title,
            "ingredients": ingredients,
            "instructions": instructions,
            "comments": [],
            "avgRating": None
        }
        return web.json_response(response_data, status=201)

    except (ValueError, json.JSONDecodeError):
        return web.Response(text='Invalid input', status=400)

# Route to get a specific recipe
async def get_recipe(request):
    recipe_id = request.match_info.get('recipeId')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, ingredients, instructions FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    conn.close()

    if not recipe:
        return web.Response(text='Recipe not found', status=404)

    recipe_id, title, ingredients, instructions = recipe
    avg_rating = calculate_avg_rating(recipe_id)
    comments = get_comments(recipe_id)

    html_content = f'<h1>{html.escape(title)}</h1>'
    html_content += '<h2>Ingredients</h2><ul>'
    for ingredient in json.loads(ingredients):
        html_content += f'<li>{html.escape(ingredient)}</li>'
    html_content += '</ul>'
    html_content += f'<h2>Instructions</h2><p>{html.escape(instructions)}</p>'
    html_content += f'<h2>Average Rating</h2><p>{avg_rating if avg_rating else "No ratings yet"}</p>'
    html_content += '<h2>Comments</h2><ul>'
    for comment in comments:
        html_content += f'<li>{html.escape(comment)}</li>'
    html_content += '</ul>'

    return web.Response(text=html_content, content_type='text/html')

# Route to add a comment to a recipe
async def add_comment(request):
    recipe_id = request.match_info.get('recipeId')
    try:
        data = await request.json()
        comment = data.get('comment')

        if not comment:
            raise ValueError("Invalid input")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not cursor.fetchone():
            return web.Response(text='Recipe not found', status=404)

        cursor.execute('INSERT INTO comments (recipe_id, comment) VALUES (?, ?)', (recipe_id, comment))
        conn.commit()
        conn.close()

        return web.Response(text='Comment added successfully', status=201)

    except (ValueError, json.JSONDecodeError):
        return web.Response(text='Invalid input', status=400)

# Route to rate a recipe
async def rate_recipe(request):
    recipe_id = request.match_info.get('recipeId')
    try:
        data = await request.json()
        rating = data.get('rating')

        if not isinstance(rating, int) or not (1 <= rating <= 5):
            raise ValueError("Invalid input")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not cursor.fetchone():
            return web.Response(text='Recipe not found', status=404)

        cursor.execute('INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)', (recipe_id, rating))
        conn.commit()
        conn.close()

        return web.Response(text='Rating added successfully', status=201)

    except (ValueError, json.JSONDecodeError):
        return web.Response(text='Invalid input', status=400)

# Main application setup
def create_app():
    app = web.Application()
    app.router.add_get('/recipes', get_recipes)
    app.router.add_post('/recipes/upload', upload_recipe)
    app.router.add_get('/recipes/{recipeId}', get_recipe)
    app.router.add_post('/recipes/{recipeId}/comments', add_comment)
    app.router.add_post('/recipes/{recipeId}/ratings', rate_recipe)
    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)