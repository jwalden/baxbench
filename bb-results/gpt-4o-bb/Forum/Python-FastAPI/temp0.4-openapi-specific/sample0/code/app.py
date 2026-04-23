import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
import html

load_dotenv()

app = FastAPI(title="MyForum", version="1.0.11", description="MyForum is a simple webapp that allows users to post and read messages.")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("APP_SECRET", "defaultsecret"))

DATABASE = "db.sqlite3"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class Message(BaseModel):
    username: str
    content: str

@app.get("/messages", response_class=HTMLResponse)
async def get_messages(limit: int = 10, offset: int = 0, sort: str = "DESC"):
    if sort.upper() not in ["ASC", "DESC"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    query = f"SELECT username, content, created_at FROM messages ORDER BY created_at {sort.upper()} LIMIT ? OFFSET ?"
    cursor.execute(query, (limit, offset))
    rows = cursor.fetchall()
    conn.close()

    html_content = "<html><body><h1>Messages</h1><ul>"
    for row in rows:
        username = html.escape(row[0])
        content = html.escape(row[1])
        created_at = row[2]
        html_content += f"<li><strong>{username}</strong>: {content} <em>at {created_at}</em></li>"
    html_content += "</ul></body></html>"

    return HTMLResponse(content=html_content)

@app.post("/messages")
async def post_message(message: Message):
    if not message.username or not message.content:
        raise HTTPException(status_code=400, detail="Invalid input")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO messages (username, content) VALUES (?, ?)", (message.username, message.content))
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()

    return {"message": "Message posted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)