import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, Query, Body
from pydantic import BaseModel
from typing import List, Dict, Any
from starlette.responses import JSONResponse

app = FastAPI(
    title="Product Catalog",
    description="Provides product catalog allowing multiple unstructured properties to be given and then searched for.",
    version="1.0.11"
)

DATABASE_FILE = 'db.sqlite3'

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
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

# Pydantic model for product
class Product(BaseModel):
    name: str
    data: Dict[str, Any]

# Add a new product to the catalog
@app.post("/add", status_code=201)
async def add_product(product: Product):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (name, data) VALUES (?, ?)', (product.name, str(product.data)))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Product already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# Download the entire current catalog for a given product name
@app.get("/download")
async def download_product(name: str = Query(...)):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM products WHERE name = ?', (name,))
        row = cursor.fetchone()
        if row:
            return JSONResponse(content={"data": row[0]})
        else:
            raise HTTPException(status_code=400, detail="Product not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# Upload data for a product
@app.post("/upload")
async def upload_product(request: Request):
    body = await request.json()
    name = body.get("name")
    data = body.get("data")
    if not name or not data:
        raise HTTPException(status_code=400, detail="Invalid upload query")
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET data = ? WHERE name = ?', (data, name))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail="Product not found")
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# Search for products in the catalog
@app.get("/search")
async def search_products(query: str = Query(...)):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT name, data FROM products WHERE name LIKE ? OR data LIKE ?', (f'%{query}%', f'%{query}%'))
        rows = cursor.fetchall()
        results = [{"name": row[0], **eval(row[1])} for row in rows]
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)