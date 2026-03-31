from fastapi import FastAPI, HTTPException, Path, Body
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder

app = FastAPI(title="Recipe Sharing App API", description="API for uploading, rating, and commenting on recipes.", version="1.0.0")

DATABASE = "db.sqlite3"

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            avgRating REAL
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

class Recipe(BaseModel):
    id: Optional[int] = None
    title: str
    ingredients: List[str]
    instructions: str
    comments: Optional[List[str]] = []
    avgRating: Optional[float] = None

class Comment(BaseModel):
    comment: str

class Rating(BaseModel):
    rating: int

@app.get("/recipes", response_class=HTMLResponse)
async def get_recipes_overview():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM recipes")
    recipes = cursor.fetchall()
    conn.close()
    
    html_content = "<h1>Recipes Overview</h1><ul>"
    for recipe in recipes:
        html_content += f'<li><a href="/recipes/{recipe[0]}">{recipe[1]}</a></li>'
    html_content += "</ul>"
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/recipes/upload", response_model=Recipe, status_code=201)
async def upload_recipe(recipe: Recipe):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO recipes (title, ingredients, instructions) VALUES (?, ?, ?)",
                   (recipe.title, ','.join(recipe.ingredients), recipe.instructions))
    conn.commit()
    recipe_id = cursor.lastrowid
    conn.close()
    recipe.id = recipe_id
    return JSONResponse(content=jsonable_encoder(recipe), status_code=201)

@app.get("/recipes/{recipeId}", response_class=HTMLResponse)
async def get_recipe(recipeId: int = Path(..., description="The ID of the recipe to retrieve")):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, ingredients, instructions, avgRating FROM recipes WHERE id = ?", (recipeId,))
    recipe = cursor.fetchone()
    if not recipe:
        conn.close()
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    cursor.execute("SELECT comment FROM comments WHERE recipe_id = ?", (recipeId,))
    comments = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    html_content = f"<h1>{recipe[1]}</h1><p>Ingredients: {recipe[2]}</p><p>Instructions: {recipe[3]}</p>"
    html_content += f"<p>Average Rating: {recipe[4]}</p><h2>Comments:</h2><ul>"
    for comment in comments:
        html_content += f"<li>{comment}</li>"
    html_content += "</ul>"
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/recipes/{recipeId}/comments", status_code=201)
async def add_comment(recipeId: int = Path(..., description="The ID of the recipe to comment on"), comment: Comment = Body(...)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipeId,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    cursor.execute("INSERT INTO comments (recipe_id, comment) VALUES (?, ?)", (recipeId, comment.comment))
    conn.commit()
    conn.close()
    return JSONResponse(content={"message": "Comment added successfully"}, status_code=201)

@app.post("/recipes/{recipeId}/ratings", status_code=201)
async def rate_recipe(recipeId: int = Path(..., description="The ID of the recipe to rate"), rating: Rating = Body(...)):
    if rating.rating < 1 or rating.rating > 5:
        raise HTTPException(status_code=400, detail="Invalid rating value")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipeId,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    cursor.execute("INSERT INTO ratings (recipe_id, rating) VALUES (?, ?)", (recipeId, rating.rating))
    cursor.execute("SELECT AVG(rating) FROM ratings WHERE recipe_id = ?", (recipeId,))
    avg_rating = cursor.fetchone()[0]
    cursor.execute("UPDATE recipes SET avgRating = ? WHERE id = ?", (avg_rating, recipeId))
    conn.commit()
    conn.close()
    return JSONResponse(content={"message": "Rating added successfully"}, status_code=201)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)