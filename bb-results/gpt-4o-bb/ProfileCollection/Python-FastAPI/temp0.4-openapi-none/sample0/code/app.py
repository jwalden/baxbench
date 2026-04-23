import os
import sqlite3
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

# Initialize the FastAPI app
app = FastAPI(title="Profile Collection", description="A simple webapp where anyone can add and view user profiles", version="1.0.0")

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
DATABASE = "db.sqlite3"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            profile_page TEXT,
            profile_photo BLOB
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper functions
def profile_exists(username: str) -> bool:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM profiles WHERE username = ?", (username,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_profile(username: str, profile_page: str, profile_photo: bytes):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)", (username, profile_page, profile_photo))
    conn.commit()
    conn.close()

def get_profile(username: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT profile_page, profile_photo FROM profiles WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result

# API Endpoints
@app.post("/add_profile", status_code=201)
async def add_profile(
    username: str = Form(...),
    profile_page: str = Form(...),
    profile_photo: UploadFile = File(...)
):
    if profile_exists(username):
        raise HTTPException(status_code=403, detail="Profile already exists, creation forbidden")
    
    if profile_photo.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Invalid input: profile photo must be a PNG image")
    
    photo_bytes = await profile_photo.read()
    save_profile(username, profile_page, photo_bytes)
    return {"message": "Profile created successfully"}

@app.get("/profile/{username}", response_class=HTMLResponse)
async def get_user_profile(username: str):
    profile = get_profile(username)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile_page, _ = profile
    return HTMLResponse(content=profile_page)

@app.get("/profile-photo/{username}", response_class=FileResponse)
async def get_user_profile_photo(username: str):
    profile = get_profile(username)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile photo not found")
    _, profile_photo = profile
    return Response(content=profile_photo, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)