import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Shopping Cart Service", description="A simple shopping cart service API.", version="1.0.0")

DATABASE = "db.sqlite3"

# Initialize the database
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

class CartResponse(BaseModel):
    cart_id: str

class CartItem(BaseModel):
    item_id: int
    count: int

class AddToCartRequest(BaseModel):
    cart_id: str
    item_id: int
    count: int

class RetrieveCartRequest(BaseModel):
    cart_id: str

class RetrieveCartResponse(BaseModel):
    items: List[CartItem]

@app.post("/create_cart", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def create_cart():
    cart_id = os.urandom(16).hex()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO carts (cart_id) VALUES (?)', (cart_id,))
    conn.commit()
    conn.close()
    return CartResponse(cart_id=cart_id)

@app.post("/add_to_cart", status_code=status.HTTP_200_OK)
async def add_to_cart(request: AddToCartRequest):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM carts WHERE cart_id = ?', (request.cart_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cursor.execute('SELECT count FROM cart_items WHERE cart_id = ? AND item_id = ?', (request.cart_id, request.item_id))
    row = cursor.fetchone()
    if row:
        new_count = row[0] + request.count
        if new_count < 0:
            conn.close()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid count")
        elif new_count == 0:
            cursor.execute('DELETE FROM cart_items WHERE cart_id = ? AND item_id = ?', (request.cart_id, request.item_id))
        else:
            cursor.execute('UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?', (new_count, request.cart_id, request.item_id))
    else:
        if request.count < 0:
            conn.close()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid count")
        cursor.execute('INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)', (request.cart_id, request.item_id, request.count))

    conn.commit()
    conn.close()
    return {"detail": "Item added or removed successfully"}

@app.post("/retrieve_cart", response_model=RetrieveCartResponse, status_code=status.HTTP_200_OK)
async def retrieve_cart(request: RetrieveCartRequest):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM carts WHERE cart_id = ?', (request.cart_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cursor.execute('SELECT item_id, count FROM cart_items WHERE cart_id = ?', (request.cart_id,))
    items = [CartItem(item_id=row[0], count=row[1]) for row in cursor.fetchall()]
    conn.close()
    return RetrieveCartResponse(items=items)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)