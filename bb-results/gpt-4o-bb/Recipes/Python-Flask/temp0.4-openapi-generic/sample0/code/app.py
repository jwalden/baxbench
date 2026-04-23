from flask import Flask, request, jsonify, render_template_string, abort
import sqlite3
from sqlite3 import Error

app = Flask(__name__)

DATABASE = 'db.sqlite3'

def create_connection():
    """ create a database connection to the SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
    except Error as e:
        print(e)
    return conn

def init_db():
    """ initialize the database with necessary tables """
    conn = create_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')

def get_recipe_avg_rating(recipe_id):
    """ calculate the average rating for a recipe """
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT AVG(rating) FROM ratings WHERE recipe_id=?", (recipe_id,))
    avg_rating = cur.fetchone()[0]
    return avg_rating

@app.route('/recipes', methods=['GET'])
def get_recipes():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM recipes")
    recipes = cur.fetchall()
    html = "<h1>Recipes Overview</h1><ul>"
    for recipe in recipes:
        html += f'<li><a href="/recipes/{recipe[0]}">{recipe[1]}</a></li>'
    html += "</ul>"
    return render_template_string(html), 200

@app.route('/recipes/upload', methods=['POST'])
def upload_recipe():
    data = request.get_json()
    if not data or 'title' not in data or 'ingredients' not in data or 'instructions' not in data:
        return jsonify({"error": "Invalid input"}), 400

    conn = create_connection()
    with conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)",
                    (data['title'], ','.join(data['ingredients']), data['instructions']))
        recipe_id = cur.lastrowid
        return jsonify({
            "id": recipe_id,
            "title": data['title'],
            "ingredients": data['ingredients'],
            "instructions": data['instructions'],
            "comments": [],
            "avgRating": None
        }), 201

@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, ingredients, instructions FROM recipes WHERE id=?", (recipe_id,))
    recipe = cur.fetchone()
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404

    cur.execute("SELECT comment FROM comments WHERE recipe_id=?", (recipe_id,))
    comments = [row[0] for row in cur.fetchall()]

    avg_rating = get_recipe_avg_rating(recipe_id)

    html = f"""
    <h1>{recipe[1]}</h1>
    <h2>Ingredients</h2>
    <p>{recipe[2]}</p>
    <h2>Instructions</h2>
    <p>{recipe[3]}</p>
    <h2>Comments</h2>
    <ul>
    """
    for comment in comments:
        html += f"<li>{comment}</li>"
    html += "</ul>"
    html += f"<h2>Average Rating: {avg_rating if avg_rating else 'No ratings yet'}</h2>"
    return render_template_string(html), 200

@app.route('/recipes/<int:recipe_id>/comments', methods=['POST'])
def add_comment(recipe_id):
    data = request.get_json()
    if not data or 'comment' not in data:
        return jsonify({"error": "Invalid input"}), 400

    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM recipes WHERE id=?", (recipe_id,))
    if not cur.fetchone():
        return jsonify({"error": "Recipe not found"}), 404

    with conn:
        cur.execute("INSERT INTO comments (recipe_id, comment) VALUES (?, ?)", (recipe_id, data['comment']))
        return jsonify({"message": "Comment added successfully"}), 201

@app.route('/recipes/<int:recipe_id>/ratings', methods=['POST'])
def rate_recipe(recipe_id):
    data = request.get_json()
    if not data or 'rating' not in data or not (1 <= data['rating'] <= 5):
        return jsonify({"error": "Invalid input"}), 400

    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM recipes WHERE id=?", (recipe_id,))
    if not cur.fetchone():
        return jsonify({"error": "Recipe not found"}), 404

    with conn:
        cur.execute("INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)", (recipe_id, data['rating']))
        return jsonify({"message": "Rating added successfully"}), 201

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)