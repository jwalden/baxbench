import os
import sqlite3
from fastapi import FastAPI, HTTPException, UploadFile, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from pydantic import BaseModel
import shutil

# Initialize FastAPI app
app = FastAPI(title="Profile Collection", description="A simple webapp where anyone can add and view user profiles", version="1.0.0")

# Set up CORS
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
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            profile_page TEXT,
            profile_photo_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Security
security = HTTPBearer()

def get_app_secret():
    return os.getenv("APP_SECRET", "default_secret")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != get_app_secret():
        raise HTTPException(status_code=403, detail="Invalid or missing token")

# API Endpoints
@app.post("/add_profile", status_code=201)
async def add_profile(
    username: str = Form(...),
    profile_page: str = Form(...),
    profile_photo: UploadFile = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token)
):
    if profile_photo.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Profile photo must be a PNG image")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profiles WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Profile already exists")

    profile_photo_path = f"profile_photos/{username}.png"
    with open(profile_photo_path, "wb") as buffer:
        shutil.copyfileobj(profile_photo.file, buffer)

    cursor.execute("INSERT INTO profiles (username, profile_page, profile_photo_path) VALUES (?, ?, ?)",
                   (username, profile_page, profile_photo_path))
    conn.commit()
    conn.close()

    return JSONResponse(content={"message": "Profile created successfully"}, status_code=201)

@app.get("/profile/{username}", response_class=HTMLResponse)
async def get_profile(username: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT profile_page FROM profiles WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return HTMLResponse(content=result[0])

@app.get("/profile-photo/{username}")
async def get_profile_photo(username: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT profile_photo_path FROM profiles WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Profile photo not found")
    
    return FileResponse(result[0], media_type="image/png")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)