from flask import Flask, request, jsonify, abort, render_template_string
import sqlite3
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        comment TEXT NOT NULL,
        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        rating INTEGER NOT NULL,
        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
    )''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/recipes', methods=['GET'])
def get_recipes():
    conn = get_db_connection()
    recipes = conn.execute('SELECT id, title FROM recipes').fetchall()
    conn.close()
    html_content = "<h1>Recipes</h1><ul>"
    for recipe in recipes:
        html_content += f'<li><a href="/recipes/{recipe["id"]}">{recipe["title"]}</a></li>'
    html_content += "</ul>"
    return render_template_string(html_content), 200

@app.route('/recipes/upload', methods=['POST'])
def upload_recipe():
    data = request.get_json()
    if not data or 'title' not in data or 'ingredients' not in data or 'instructions' not in data:
        abort(400, description="Invalid input")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)',
                   (data['title'], ','.join(data['ingredients']), data['instructions']))
    conn.commit()
    recipe_id = cursor.lastrowid
    conn.close()
    
    return jsonify({"id": recipe_id, "title": data['title'], "ingredients": data['ingredients'], "instructions": data['instructions']}), 201

@app.route('/recipes/<int:recipeId>', methods=['GET'])
def get_recipe(recipeId):
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (recipeId,)).fetchone()
    if recipe is None:
        conn.close()
        abort(404, description="Recipe not found")
    
    comments = conn.execute('SELECT comment FROM comments WHERE recipe_id = ?', (recipeId,)).fetchall()
    ratings = conn.execute('SELECT rating FROM ratings WHERE recipe_id = ?', (recipeId,)).fetchall()
    conn.close()
    
    avg_rating = None
    if ratings:
        avg_rating = sum(rating['rating'] for rating in ratings) / len(ratings)
    
    html_content = f"<h1>{recipe['title']}</h1><p>{recipe['instructions']}</p><h2>Ingredients:</h2><ul>"
    for ingredient in recipe['ingredients'].split(','):
        html_content += f"<li>{ingredient}</li>"
    html_content += "</ul><h2>Comments:</h2><ul>"
    for comment in comments:
        html_content += f"<li>{comment['comment']}</li>"
    html_content += "</ul><h2>Average Rating:</h2><p>{avg_rating if avg_rating is not None else 'No ratings yet'}</p>"
    
    return render_template_string(html_content), 200

@app.route('/recipes/<int:recipeId>/comments', methods=['POST'])
def add_comment(recipeId):
    data = request.get_json()
    if not data or 'comment' not in data:
        abort(400, description="Invalid input")
    
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (recipeId,)).fetchone()
    if recipe is None:
        conn.close()
        abort(404, description="Recipe not found")
    
    conn.execute('INSERT INTO comments (recipe_id, comment) VALUES (?, ?)', (recipeId, data['comment']))
    conn.commit()
    conn.close()
    
    return '', 201

@app.route('/recipes/<int:recipeId>/ratings', methods=['POST'])
def rate_recipe(recipeId):
    data = request.get_json()
    if not data or 'rating' not in data or not (1 <= data['rating'] <= 5):
        abort(400, description="Invalid input")
    
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (recipeId,)).fetchone()
    if recipe is None:
        conn.close()
        abort(404, description="Recipe not found")
    
    conn.execute('INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)', (recipeId, data['rating']))
    conn.commit()
    conn.close()
    
    return '', 201

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = jsonify({"error": e.description}).data
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)