import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

DATABASE = "db.sqlite3"

app = FastAPI(title="Click Tracking API", version="1.0.0", description="API for registering and retrieving user clicks.")

# Ensure the database and table exist
def init_db():
    conn = sqlite3.connect(DATABASE)
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

class Click(BaseModel):
    id: int
    timestamp: datetime

@app.post("/click", status_code=HTTP_201_CREATED)
def register_click():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        cursor.execute("INSERT INTO clicks (timestamp) VALUES (?)", (timestamp,))
        conn.commit()
        conn.close()
        return JSONResponse(status_code=HTTP_201_CREATED, content={"message": "Click registered successfully"})
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))

@app.get("/clicks", response_model=list[Click])
def retrieve_clicks(date: str = Query(..., description="The date to filter clicks.", example="2022-01-01"), 
                    direction: str = Query(..., description="Specify '<', '<=' or '>' etc. to filter clicks before, before or at or after the date.", enum=["<", ">", "<=", ">="])):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        query = f"SELECT id, timestamp FROM clicks WHERE timestamp {direction} ?"
        cursor.execute(query, (date,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No clicks found")
        
        clicks = [Click(id=row[0], timestamp=row[1]) for row in rows]
        return clicks
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)