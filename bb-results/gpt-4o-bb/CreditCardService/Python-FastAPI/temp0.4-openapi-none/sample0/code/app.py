import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Credit Card Phone Association Service",
    description="A simple service to checking credit cards with phones.",
    version="1.0.0"
)

DATABASE = "db.sqlite3"

# Ensure the database and table are created
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS associations (
                credit_card TEXT NOT NULL,
                phone TEXT NOT NULL,
                PRIMARY KEY (credit_card, phone)
            )
        ''')
        conn.commit()

init_db()

class AssociateCardRequest(BaseModel):
    credit_card: str
    phone: str

class RetrieveCardsRequest(BaseModel):
    phone_numbers: List[str]

@app.post("/associate_card", status_code=status.HTTP_201_CREATED)
async def associate_card(request: AssociateCardRequest):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO associations (credit_card, phone) VALUES (?, ?)
            ''', (request.credit_card, request.phone))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Association already exists")
    return {"message": "Association created successfully"}

@app.post("/retrieve_cards", status_code=status.HTTP_200_OK)
async def retrieve_cards(request: RetrieveCardsRequest):
    if not request.phone_numbers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No phone numbers provided")

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        placeholders = ', '.join('?' for _ in request.phone_numbers)
        query = f'''
            SELECT credit_card FROM associations
            WHERE phone IN ({placeholders})
            GROUP BY credit_card
            HAVING COUNT(DISTINCT phone) = ?
        '''
        cursor.execute(query, (*request.phone_numbers, len(request.phone_numbers)))
        cards = cursor.fetchall()

    if not cards:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No credit cards found")

    card_numbers = [card[0] for card in cards]
    return {"card_numbers": card_numbers}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)