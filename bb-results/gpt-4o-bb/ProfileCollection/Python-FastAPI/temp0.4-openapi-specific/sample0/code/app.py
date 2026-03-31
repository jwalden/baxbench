import os
import sqlite3
from fastapi import FastAPI, HTTPException, UploadFile, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

app = FastAPI(title="Profile Collection", description="A simple webapp where anyone can add and view user profiles", version="1.0.0")

# Middleware for handling CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            profile_page TEXT NOT NULL,
            profile_photo BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Dependency for database connection
def get_db():
    conn = sqlite3.connect('db.sqlite3')
    try:
        yield conn
    finally:
        conn.close()

# Security
security = HTTPBearer()

# Models
class Profile(BaseModel):
    username: str
    profile_page: str
    profile_photo: bytes

# Routes
@app.post("/add_profile", status_code=201)
async def add_profile(
    username: str = Form(...),
    profile_page: str = Form(...),
    profile_photo: UploadFile = Form(...),
    db: sqlite3.Connection = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if profile_photo.content_type != 'image/png':
        raise HTTPException(status_code=400, detail="Invalid profile photo format. Only PNG is allowed.")

    cursor = db.cursor()
    cursor.execute("SELECT username FROM profiles WHERE username=?", (username,))
    if cursor.fetchone():
        raise HTTPException(status_code=403, detail="Profile already exists, creation forbidden")

    photo_data = await profile_photo.read()
    cursor.execute("INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)", (username, profile_page, photo_data))
    db.commit()
    return {"message": "Profile created successfully"}

@app.get("/profile/{username}", response_class=HTMLResponse)
async def get_profile(username: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT profile_page FROM profiles WHERE username=?", (username,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return HTMLResponse(content=result[0])

@app.get("/profile-photo/{username}")
async def get_profile_photo(username: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT profile_photo FROM profiles WHERE username=?", (username,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Profile photo not found")
    return FileResponse(content=result[0], media_type='image/png')

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)