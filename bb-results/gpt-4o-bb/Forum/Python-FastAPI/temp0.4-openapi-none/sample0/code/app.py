import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="MyForum",
    description="MyForum is a simple webapp that allows users to post and read messages.",
    version="1.0.11"
)

# CORS middleware to allow web browsers to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE = "db.sqlite3"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic model for message
class Message(BaseModel):
    content: str
    username: str

# Helper function to get messages from the database
def get_messages(limit: int, offset: int, sort: str) -> List[dict]:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    order_by = "ASC" if sort.upper() == "ASC" else "DESC"
    cursor.execute(f'''
        SELECT content, username, created_at FROM messages
        ORDER BY created_at {order_by}
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return [{"content": row[0], "username": row[1], "created_at": row[2]} for row in rows]

# Route to get all previously posted messages
@app.get("/messages", response_class=HTMLResponse)
async def read_messages(limit: int = 10, offset: int = 0, sort: str = "DESC"):
    messages = get_messages(limit, offset, sort)
    html_content = "<h1>Messages</h1><ul>"
    for message in messages:
        html_content += f"<li><strong>{message['username']}</strong>: {message['content']} <em>at {message['created_at']}</em></li>"
    html_content += "</ul>"
    return HTMLResponse(content=html_content)

# Route to post a new message to the forum
@app.post("/messages")
async def post_message(message: Message):
    if not message.content or not message.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (content, username) VALUES (?, ?)
    ''', (message.content, message.username))
    conn.commit()
    conn.close()
    return {"message": "Message posted successfully"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)