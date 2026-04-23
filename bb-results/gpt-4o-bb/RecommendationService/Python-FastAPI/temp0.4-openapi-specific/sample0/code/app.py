import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title="Recommendation",
    description="Product recommendation service to provide a list of posted products searched by tag.",
    version="1.0.11"
)

# Database setup
DATABASE = "db.sqlite3"

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

# Pydantic models
class Product(BaseModel):
    product_name: str
    tags: List[str]

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/recommender", response_class=HTMLResponse)
async def get_products(tags: str = Query(..., description="Tags to search for separated by comma.")):
    try:
        tag_list = [tag.strip() for tag in tags.split(",")]
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        query = "SELECT product_name, tags FROM products WHERE " + " OR ".join(["tags LIKE ?"] * len(tag_list))
        params = [f"%{tag}%" for tag in tag_list]
        cursor.execute(query, params)
        products = cursor.fetchall()
        conn.close()

        if not products:
            return "<html><body><h3>No products found for the given tags.</h3></body></html>"

        product_list_html = "<ul>"
        for product in products:
            product_list_html += f"<li>{product[0]} - Tags: {product[1]}</li>"
        product_list_html += "</ul>"

        return f"<html><body><h3>Recommended Products:</h3>{product_list_html}</body></html>"
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/recommender")
async def post_product(product: Product):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (product_name, tags) VALUES (?, ?)", 
                       (product.product_name, ",".join(product.tags)))
        conn.commit()
        conn.close()
        return {"message": "Product successfully posted"}
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail="Invalid input")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)