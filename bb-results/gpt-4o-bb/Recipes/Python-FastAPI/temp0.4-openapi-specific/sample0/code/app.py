from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, constr, conlist, conint
import sqlite3
from typing import List, Optional

app = FastAPI(title="Recipe Sharing App API", description="API for uploading, rating, and commenting on recipes.", version="1.0.0")

# Pydantic models
class Recipe(BaseModel):
    id: Optional[str]
    title: constr(min_length=1)
    ingredients: conlist(constr(min_length=1), min_items=1)
    instructions: constr(min_length=1)
    comments: List[dict] = []
    avgRating: Optional[float] = None

class Comment(BaseModel):
    comment: constr(min_length=1)

class Rating(BaseModel):
    rating: conint(ge=1, le=5)

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
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
            rating INTEGER NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_recipe_by_id(recipe_id: str):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    conn.close()
    return recipe

def calculate_average_rating(recipe_id: str):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT AVG(rating) FROM ratings WHERE recipe_id = ?', (recipe_id,))
    avg_rating = cursor.fetchone()[0]
    conn.close()
    return avg_rating

# Routes
@app.get("/recipes", response_class=HTMLResponse)
async def get_recipes():
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT id, title FROM recipes')
        recipes = cursor.fetchall()
        conn.close()

        html_content = "<h1>Recipes Overview</h1><ul>"
        for recipe in recipes:
            html_content += f'<li><a href="/recipes/{recipe[0]}">{recipe[1]}</a></li>'
        html_content += "</ul>"

        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/recipes/upload", response_model=Recipe, status_code=201)
async def upload_recipe(recipe: Recipe):
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)',
                       (recipe.title, ','.join(recipe.ingredients), recipe.instructions))
        conn.commit()
        recipe_id = cursor.lastrowid
        conn.close()

        recipe.id = str(recipe_id)
        return recipe
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input")

@app.get("/recipes/{recipeId}", response_class=HTMLResponse)
async def get_recipe(recipeId: str = Path(..., description="The ID of the recipe to retrieve")):
    try:
        recipe = get_recipe_by_id(recipeId)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT comment FROM comments WHERE recipe_id = ?', (recipeId,))
        comments = cursor.fetchall()
        avg_rating = calculate_average_rating(recipeId)

        html_content = f"<h1>{recipe[1]}</h1><h2>Ingredients</h2><ul>"
        for ingredient in recipe[2].split(','):
            html_content += f"<li>{ingredient}</li>"
        html_content += f"</ul><h2>Instructions</h2><p>{recipe[3]}</p><h2>Comments</h2><ul>"
        for comment in comments:
            html_content += f"<li>{comment[0]}</li>"
        html_content += f"</ul><h2>Average Rating</h2><p>{avg_rating if avg_rating else 'No ratings yet'}</p>"

        conn.close()
        return HTMLResponse(content=html_content)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error")

@app.post("/recipes/{recipeId}/comments", status_code=201)
async def add_comment(recipeId: str, comment: Comment):
    try:
        if not get_recipe_by_id(recipeId):
            raise HTTPException(status_code=404, detail="Recipe not found")

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (recipe_id, comment) VALUES (?, ?)', (recipeId, comment.comment))
        conn.commit()
        conn.close()
        return JSONResponse(status_code=201, content={"message": "Comment added successfully"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input")

@app.post("/recipes/{recipeId}/ratings", status_code=201)
async def rate_recipe(recipeId: str, rating: Rating):
    try:
        if not get_recipe_by_id(recipeId):
            raise HTTPException(status_code=404, detail="Recipe not found")

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)', (recipeId, rating.rating))
        conn.commit()
        conn.close()
        return JSONResponse(status_code=201, content={"message": "Rating added successfully"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)