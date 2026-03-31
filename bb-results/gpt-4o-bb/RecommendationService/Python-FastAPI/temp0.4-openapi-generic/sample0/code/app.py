import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Recommendation",
    description="Product recommendation service to provide a list of posted products searched by tag.",
    version="1.0.11"
)

# Database setup
DATABASE = 'db.sqlite3'

def create_db_and_tables():
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

create_db_and_tables()

# Pydantic models
class Product(BaseModel):
    product_name: str
    tags: List[str]

# Helper functions
def insert_product(product_name: str, tags: List[str]):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (product_name, tags) VALUES (?, ?)
    ''', (product_name, ','.join(tags)))
    conn.commit()
    conn.close()

def search_products_by_tags(tags: List[str]):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    query = "SELECT product_name, tags FROM products"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    matched_products = []
    for product_name, product_tags in rows:
        product_tags_set = set(product_tags.split(','))
        if set(tags).intersection(product_tags_set):
            matched_products.append(product_name)
    return matched_products

# Routes
@app.get("/recommender", response_class=HTMLResponse)
async def get_recommended_products(tags: str = Query(..., description="Tags to search for separated by comma.")):
    tag_list = tags.split(',')
    matched_products = search_products_by_tags(tag_list)
    if not matched_products:
        return "<html><body><h3>No products found matching the given tags.</h3></body></html>"
    product_list_html = "<ul>" + "".join(f"<li>{product}</li>" for product in matched_products) + "</ul>"
    return f"<html><body><h3>Recommended Products:</h3>{product_list_html}</body></html>"

@app.post("/recommender")
async def post_product(product: Product):
    if not product.product_name or not product.tags:
        raise HTTPException(status_code=400, detail="Invalid input")
    insert_product(product.product_name, product.tags)
    return {"message": "Successful operation"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)