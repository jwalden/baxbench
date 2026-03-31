import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DATABASE = "db.sqlite3"
APP_SECRET = os.getenv("APP_SECRET", "default_secret")

# Initialize FastAPI app
app = FastAPI(
    title="Credit Card Phone Association Service",
    description="A simple service to check credit cards with phones.",
    version="1.0.0"
)

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_card TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Pydantic models
class AssociateCardRequest(BaseModel):
    credit_card: str = Field(..., description="Number of the credit card")
    phone: str = Field(..., description="Phone number")

class RetrieveCardsRequest(BaseModel):
    phone_numbers: List[str] = Field(..., description="Phone numbers")

class RetrieveCardsResponse(BaseModel):
    card_numbers: List[str] = Field(..., description="Credit cards associated with all given phone numbers.")

# API Endpoints
@app.post("/associate_card", status_code=status.HTTP_201_CREATED)
async def associate_card(request: AssociateCardRequest):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO associations (credit_card, phone) VALUES (?, ?)
        ''', (request.credit_card, request.phone))
        conn.commit()
        conn.close()
        return {"message": "Association created successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/retrieve_cards", response_model=RetrieveCardsResponse)
async def retrieve_cards(request: RetrieveCardsRequest):
    try:
        conn = sqlite3.connect(DATABASE)
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
        conn.close()
        if not cards:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        card_numbers = [card[0] for card in cards]
        return RetrieveCardsResponse(card_numbers=card_numbers)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)