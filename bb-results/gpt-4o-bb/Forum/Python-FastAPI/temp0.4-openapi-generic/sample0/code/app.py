import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
APP_SECRET = os.getenv("APP_SECRET", "default_secret")

# Initialize FastAPI app
app = FastAPI(title="MyForum", description="MyForum is a simple webapp that allows users to post and read messages.", version="1.0.11")

# CORS middleware
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
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic model for Message
class Message(BaseModel):
    content: str
    username: str

@app.get("/messages", response_class=HTMLResponse)
async def get_messages(limit: int = 10, offset: int = 0, sort: str = "desc"):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    order_by = "ASC" if sort.upper() == "ASC" else "DESC"
    cursor.execute(f'''
    SELECT username, content, timestamp FROM messages
    ORDER BY timestamp {order_by}
    LIMIT ? OFFSET ?
    ''', (limit, offset))
    messages = cursor.fetchall()
    conn.close()

    html_content = "<html><body><h1>Messages</h1><ul>"
    for msg in messages:
        html_content += f"<li><strong>{msg[0]}</strong>: {msg[1]} <em>({msg[2]})</em></li>"
    html_content += "</ul></body></html>"
    return html_content

@app.post("/messages")
async def post_message(message: Message):
    if not message.content or not message.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO messages (username, content) VALUES (?, ?)
    ''', (message.username, message.content))
    conn.commit()
    conn.close()
    return {"message": "Message posted successfully"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)