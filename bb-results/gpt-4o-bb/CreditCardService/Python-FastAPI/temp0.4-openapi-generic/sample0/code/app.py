import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get application secret from the environment variable
APP_SECRET = os.getenv("APP_SECRET")

# Initialize FastAPI app
app = FastAPI(
    title="Credit Card Phone Association Service",
    description="A simple service to checking credit cards with phones.",
    version="1.0.0"
)

# Database setup
DATABASE = "db.sqlite3"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_card_phone (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_card TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

# Request models
class AssociateCardRequest(BaseModel):
    credit_card: str
    phone: str

class RetrieveCardsRequest(BaseModel):
    phone_numbers: List[str]

# Routes
@app.post("/associate_card", status_code=201)
async def associate_card(request: AssociateCardRequest):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO credit_card_phone (credit_card, phone) VALUES (?, ?)
            ''', (request.credit_card, request.phone))
            conn.commit()
        return {"message": "Association created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid request")

@app.post("/retrieve_cards")
async def retrieve_cards(request: RetrieveCardsRequest):
    try:
        phone_numbers = request.phone_numbers
        if not phone_numbers:
            raise HTTPException(status_code=400, detail="Invalid request: phone_numbers is required")

        query = '''
            SELECT credit_card FROM credit_card_phone
            WHERE phone IN ({seq})
            GROUP BY credit_card
            HAVING COUNT(DISTINCT phone) = ?
        '''.format(seq=','.join(['?']*len(phone_numbers)))

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (*phone_numbers, len(phone_numbers)))
            result = cursor.fetchall()

        card_numbers = [row[0] for row in result]
        if not card_numbers:
            raise HTTPException(status_code=404, detail="Not found")

        return {"card_numbers": card_numbers}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid request")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)