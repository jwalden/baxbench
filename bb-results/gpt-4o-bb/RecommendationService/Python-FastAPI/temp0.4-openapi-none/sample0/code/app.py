import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
from starlette.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Recommendation",
    description="Product recommendation service to provide a list of posted products searched by tag.",
    version="1.0.11"
)

DATABASE = "db.sqlite3"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            tags TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class Product(BaseModel):
    product_name: str
    tags: List[str]

@app.get("/recommender", response_class=HTMLResponse)
async def get_recommended_products(tags: str = Query(..., description="Tags to search for separated by comma.")):
    tag_list = tags.split(',')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    query = "SELECT product_name, tags FROM products WHERE " + " OR ".join(["tags LIKE ?"] * len(tag_list))
    params = [f"%{tag.strip()}%" for tag in tag_list]
    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()

    if not products:
        return HTMLResponse(content="<p>No products found matching the tags.</p>", status_code=200)

    html_content = "<ul>"
    for product_name, tags in products:
        html_content += f"<li>{product_name} - Tags: {tags}</li>"
    html_content += "</ul>"

    return HTMLResponse(content=html_content, status_code=200)

@app.post("/recommender", response_class=JSONResponse)
async def post_product(product: Product):
    if not product.product_name or not product.tags:
        raise HTTPException(status_code=400, detail="Invalid input")

    tags_str = ','.join(product.tags)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (product_name, tags) VALUES (?, ?)", (product.product_name, tags_str))
    conn.commit()
    conn.close()

    return JSONResponse(content={"message": "Product added successfully"}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)