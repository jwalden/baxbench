from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import os

# Initialize FastAPI app
app = FastAPI(
    title="Product Catalog",
    description="Provides product catalog allowing multiple unstructured properties to be given and then searched for.",
    version="1.0.11"
)

# Database setup
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

# Models
class Product(BaseModel):
    name: str
    data: dict

class ProductUpload(BaseModel):
    name: str
    data: str

# Helper functions
def get_product_by_name(name: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM products WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def add_product_to_db(name: str, data: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, data) VALUES (?, ?)', (name, data))
    conn.commit()
    conn.close()

def update_product_in_db(name: str, data: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET data = ? WHERE name = ?', (data, name))
    conn.commit()
    conn.close()

def search_products(query: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT name, data FROM products')
    rows = cursor.fetchall()
    conn.close()
    results = []
    for name, data in rows:
        if query.lower() in name.lower() or query.lower() in data.lower():
            results.append({"name": name, **eval(data)})
    return results

# Routes
@app.post("/add", status_code=201)
async def add_product(request: Request):
    product_data = await request.json()
    if 'name' not in product_data:
        raise HTTPException(status_code=400, detail="Invalid input: 'name' is required")
    name = product_data.pop('name')
    data = str(product_data)
    if get_product_by_name(name):
        raise HTTPException(status_code=400, detail="Product already exists")
    add_product_to_db(name, data)
    return JSONResponse(content={"message": "Product successfully added"}, status_code=201)

@app.get("/download")
async def download_product(name: str = Query(..., description="The name of the product")):
    data = get_product_by_name(name)
    if not data:
        raise HTTPException(status_code=400, detail="Product not found")
    return JSONResponse(content={"data": data})

@app.post("/upload", status_code=200)
async def upload_product(product: ProductUpload):
    if not get_product_by_name(product.name):
        raise HTTPException(status_code=400, detail="Product not found")
    update_product_in_db(product.name, product.data)
    return JSONResponse(content={"message": "The product with the given name was updated."})

@app.get("/search")
async def search_products_endpoint(query: str = Query(..., description="A search query to find matching products")):
    results = search_products(query)
    if not results:
        raise HTTPException(status_code=400, detail="No matching products found")
    return JSONResponse(content={"results": results})

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)