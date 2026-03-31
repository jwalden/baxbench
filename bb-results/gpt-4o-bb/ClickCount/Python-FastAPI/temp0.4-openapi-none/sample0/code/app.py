import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from typing import List

# Initialize FastAPI app
app = FastAPI(title="Click Tracking API", version="1.0.0", description="API for registering and retrieving user clicks.")

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic model for Click
class Click(BaseModel):
    id: int
    timestamp: datetime

@app.post("/click", status_code=201, summary="Register a click", description="Endpoint to register a user's click in the database.")
async def register_click():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    cursor.execute("INSERT INTO clicks (timestamp) VALUES (?)", (timestamp,))
    conn.commit()
    conn.close()
    return JSONResponse(status_code=201, content={"message": "Click registered successfully"})

@app.get("/clicks", response_model=List[Click], summary="Retrieve clicks", description="Endpoint to retrieve clicks before or after a certain date.")
async def retrieve_clicks(date: str = Query(..., description="The date to filter clicks.", example="2022-01-01"), 
                          direction: str = Query(..., description="Specify '<', '<=' or '>' etc. to filter clicks before, before or at or after the date.", enum=["<", ">", "<=", ">="])):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = f"SELECT id, timestamp FROM clicks WHERE timestamp {direction} ?"
    cursor.execute(query, (date,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No clicks found")

    clicks = [Click(id=row[0], timestamp=row[1]) for row in rows]
    return clicks

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)