import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Dict, Any, List
from fastapi.responses import JSONResponse

# Initialize FastAPI app
app = FastAPI(
    title="Product Catalog",
    description="Provides product catalog allowing multiple unstructured properties to be given and then searched for.",
    version="1.0.11"
)

# Database initialization
DATABASE = "db.sqlite3"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            name TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class Product(BaseModel):
    name: str
    __root__: Dict[str, Any] = {}

class ProductData(BaseModel):
    name: str
    data: str

# Helper functions
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

# Routes
@app.post("/add", status_code=201)
async def add_product(product: Product):
    conn = get_db_connection()
    cursor = conn.cursor()
    product_data = product.dict()
    name = product_data.pop("name")
    data = str(product_data)
    
    try:
        cursor.execute("INSERT INTO products (name, data) VALUES (?, ?)", (name, data))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Product with this name already exists.")
    
    conn.close()
    return {"message": "Product successfully added"}

@app.get("/download")
async def download_product(name: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM products WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return JSONResponse(content={"data": row[0]})
    else:
        raise HTTPException(status_code=400, detail="Product not found.")

@app.post("/upload")
async def upload_product(product_data: ProductData):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM products WHERE name = ?", (product_data.name,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=400, detail="Product not found.")
    
    cursor.execute("UPDATE products SET data = ? WHERE name = ?", (product_data.data, product_data.name))
    conn.commit()
    conn.close()
    
    return {"message": "The product with the given name was updated."}

@app.get("/search")
async def search_products(query: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, data FROM products")
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for name, data in rows:
        product_data = eval(data)
        if query.lower() in name.lower() or any(query.lower() in str(value).lower() for value in product_data.values()):
            results.append({"name": name, **product_data})
    
    if not results:
        raise HTTPException(status_code=400, detail="No matching products found.")
    
    return JSONResponse(content={"results": results})

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)