from flask import Flask, request, jsonify, render_template_string, abort
import sqlite3
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

DATABASE = 'db.sqlite3'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.before_first_request
def initialize():
    init_db()

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), e.code
    return jsonify(error="Internal Server Error"), 500

@app.route('/recipes', methods=['GET'])
def get_recipes():
    try:
        db = get_db()
        cur = db.execute('SELECT id, title FROM recipes ORDER BY id DESC')
        recipes = cur.fetchall()
        recipe_list = [{'id': row['id'], 'title': row['title']} for row in recipes]
        html_content = "<h1>Recipes</h1><ul>" + "".join(
            f"<li><a href='/recipes/{r['id']}'>{r['title']}</a></li>" for r in recipe_list
        ) + "</ul>"
        return render_template_string(html_content), 200
    except Exception as e:
        return handle_exception(e)

@app.route('/recipes/upload', methods=['POST'])
def upload_recipe():
    try:
        data = request.json
        title = data.get('title')
        ingredients = data.get('ingredients')
        instructions = data.get('instructions')

        if not title or not ingredients or not instructions:
            abort(400, description="Invalid input")

        db = get_db()
        db.execute('INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)',
                   (title, ','.join(ingredients), instructions))
        db.commit()

        return jsonify({"message": "Recipe created successfully"}), 201
    except Exception as e:
        return handle_exception(e)

@app.route('/recipes/<recipeId>', methods=['GET'])
def get_recipe(recipeId):
    try:
        db = get_db()
        cur = db.execute('SELECT * FROM recipes WHERE id = ?', (recipeId,))
        recipe = cur.fetchone()

        if recipe is None:
            abort(404, description="Recipe not found")

        comments_cur = db.execute('SELECT comment FROM comments WHERE recipe_id = ?', (recipeId,))
        comments = [row['comment'] for row in comments_cur.fetchall()]

        html_content = f"""
        <h1>{recipe['title']}</h1>
        <p><strong>Ingredients:</strong> {recipe['ingredients']}</p>
        <p><strong>Instructions:</strong> {recipe['instructions']}</p>
        <p><strong>Comments:</strong> {', '.join(comments)}</p>
        """
        return render_template_string(html_content), 200
    except Exception as e:
        return handle_exception(e)

@app.route('/recipes/<recipeId>/comments', methods=['POST'])
def add_comment(recipeId):
    try:
        data = request.json
        comment = data.get('comment')

        if not comment:
            abort(400, description="Invalid input")

        db = get_db()
        cur = db.execute('SELECT id FROM recipes WHERE id = ?', (recipeId,))
        if cur.fetchone() is None:
            abort(404, description="Recipe not found")

        db.execute('INSERT INTO comments (recipe_id, comment) VALUES (?, ?)', (recipeId, comment))
        db.commit()

        return jsonify({"message": "Comment added successfully"}), 201
    except Exception as e:
        return handle_exception(e)

@app.route('/recipes/<recipeId>/ratings', methods=['POST'])
def rate_recipe(recipeId):
    try:
        data = request.json
        rating = data.get('rating')

        if not isinstance(rating, int) or rating < 1 or rating > 5:
            abort(400, description="Invalid input")

        db = get_db()
        cur = db.execute('SELECT id FROM recipes WHERE id = ?', (recipeId,))
        if cur.fetchone() is None:
            abort(404, description="Recipe not found")

        db.execute('INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)', (recipeId, rating))
        db.commit()

        return jsonify({"message": "Rating added successfully"}), 201
    except Exception as e:
        return handle_exception(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)