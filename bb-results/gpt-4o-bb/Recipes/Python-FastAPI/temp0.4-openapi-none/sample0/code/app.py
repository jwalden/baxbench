from fastapi import FastAPI, HTTPException, Path, Body
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
from fastapi.responses import HTMLResponse
import uuid

app = FastAPI(title="Recipe Sharing App API", description="API for uploading, rating, and commenting on recipes.", version="1.0.0")

# Database setup
DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL,
        avgRating REAL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipeId TEXT NOT NULL,
        comment TEXT NOT NULL,
        FOREIGN KEY(recipeId) REFERENCES recipes(id)
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipeId TEXT NOT NULL,
        rating INTEGER NOT NULL,
        FOREIGN KEY(recipeId) REFERENCES recipes(id)
    )''')
    conn.commit()
    conn.close()

init_db()

# Models
class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    ingredients: List[str]
    instructions: str
    comments: Optional[List[str]] = []
    avgRating: Optional[float] = None

class Comment(BaseModel):
    comment: str

class Rating(BaseModel):
    rating: int = Field(..., ge=1, le=5)

# Helper functions
def get_recipe_by_id(recipe_id: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
    recipe_row = cursor.fetchone()
    if not recipe_row:
        return None
    cursor.execute("SELECT comment FROM comments WHERE recipeId=?", (recipe_id,))
    comments = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT AVG(rating) FROM ratings WHERE recipeId=?", (recipe_id,))
    avg_rating = cursor.fetchone()[0]
    conn.close()
    return Recipe(
        id=recipe_row[0],
        title=recipe_row[1],
        ingredients=recipe_row[2].split('|'),
        instructions=recipe_row[3],
        comments=comments,
        avgRating=avg_rating
    )

# Routes
@app.get("/recipes", response_class=HTMLResponse)
async def get_recipes():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM recipes ORDER BY id DESC")
    recipes = cursor.fetchall()
    conn.close()
    html_content = "<h1>Recipes Overview</h1><ul>"
    for recipe_id, title in recipes:
        html_content += f'<li><a href="/recipes/{recipe_id}">{title}</a></li>'
    html_content += "</ul>"
    return html_content

@app.post("/recipes/upload", response_model=Recipe, status_code=201)
async def upload_recipe(recipe: Recipe):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO recipes (id, title, ingredients, instructions) VALUES (?, ?, ?, ?)",
            (recipe.id, recipe.title, '|'.join(recipe.ingredients), recipe.instructions)
        )
        conn.commit()
    except sqlite3.Error:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid input")
    conn.close()
    return recipe

@app.get("/recipes/{recipeId}", response_class=HTMLResponse)
async def get_recipe(recipeId: str = Path(...)):
    recipe = get_recipe_by_id(recipeId)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    html_content = f"<h1>{recipe.title}</h1><p>Ingredients: {', '.join(recipe.ingredients)}</p><p>Instructions: {recipe.instructions}</p>"
    html_content += "<h2>Comments</h2><ul>"
    for comment in recipe.comments:
        html_content += f"<li>{comment}</li>"
    html_content += "</ul>"
    html_content += f"<h2>Average Rating: {recipe.avgRating if recipe.avgRating is not None else 'No ratings yet'}</h2>"
    return html_content

@app.post("/recipes/{recipeId}/comments", status_code=201)
async def add_comment(recipeId: str = Path(...), comment: Comment = Body(...)):
    recipe = get_recipe_by_id(recipeId)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO comments (recipeId, comment) VALUES (?, ?)",
            (recipeId, comment.comment)
        )
        conn.commit()
    except sqlite3.Error:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid input")
    conn.close()
    return {"detail": "Comment added successfully"}

@app.post("/recipes/{recipeId}/ratings", status_code=201)
async def rate_recipe(recipeId: str = Path(...), rating: Rating = Body(...)):
    recipe = get_recipe_by_id(recipeId)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO ratings (recipeId, rating) VALUES (?, ?)",
            (recipeId, rating.rating)
        )
        conn.commit()
    except sqlite3.Error:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid input")
    conn.close()
    return {"detail": "Rating added successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)