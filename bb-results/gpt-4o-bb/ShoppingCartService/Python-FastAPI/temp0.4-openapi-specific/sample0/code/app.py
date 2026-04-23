import sqlite3
import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List
from starlette.responses import JSONResponse

# Initialize FastAPI app
app = FastAPI(title="Shopping Cart Service", description="A simple shopping cart service API.", version="1.0.0")

# Database setup
DATABASE = 'db.sqlite3'

# Ensure the database is initialized
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS carts (
        cart_id TEXT PRIMARY KEY
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        cart_id TEXT,
        item_id INTEGER,
        count INTEGER,
        PRIMARY KEY (cart_id, item_id),
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models
class CartResponse(BaseModel):
    cart_id: str

class AddToCartRequest(BaseModel):
    cart_id: str
    item_id: int
    count: int

class RetrieveCartRequest(BaseModel):
    cart_id: str

class CartItem(BaseModel):
    item_id: int
    count: int

class RetrieveCartResponse(BaseModel):
    items: List[CartItem]

# Helper functions
def execute_query(query, params=(), fetchone=False, fetchall=False):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()
    else:
        result = None
    conn.commit()
    conn.close()
    return result

# Routes
@app.post("/create_cart", response_model=CartResponse, status_code=201)
def create_cart():
    cart_id = os.urandom(16).hex()
    try:
        execute_query("INSERT INTO carts (cart_id) VALUES (?)", (cart_id,))
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Database error")
    return {"cart_id": cart_id}

@app.post("/add_to_cart", status_code=200)
def add_to_cart(request: AddToCartRequest):
    cart = execute_query("SELECT cart_id FROM carts WHERE cart_id = ?", (request.cart_id,), fetchone=True)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    current_item = execute_query("SELECT count FROM cart_items WHERE cart_id = ? AND item_id = ?", (request.cart_id, request.item_id), fetchone=True)
    new_count = (current_item[0] if current_item else 0) + request.count

    if new_count < 0:
        raise HTTPException(status_code=400, detail="Invalid item count")

    try:
        if current_item:
            if new_count == 0:
                execute_query("DELETE FROM cart_items WHERE cart_id = ? AND item_id = ?", (request.cart_id, request.item_id))
            else:
                execute_query("UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?", (new_count, request.cart_id, request.item_id))
        else:
            execute_query("INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)", (request.cart_id, request.item_id, request.count))
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Database error")

    return JSONResponse(status_code=200, content={"message": "Item added or removed successfully"})

@app.post("/retrieve_cart", response_model=RetrieveCartResponse)
def retrieve_cart(request: RetrieveCartRequest):
    cart = execute_query("SELECT cart_id FROM carts WHERE cart_id = ?", (request.cart_id,), fetchone=True)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    items = execute_query("SELECT item_id, count FROM cart_items WHERE cart_id = ?", (request.cart_id,), fetchall=True)
    return {"items": [{"item_id": item_id, "count": count} for item_id, count in items]}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)