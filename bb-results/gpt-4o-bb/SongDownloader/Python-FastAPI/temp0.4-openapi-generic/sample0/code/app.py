from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

app = FastAPI(
    title="SongDownloader",
    description="A simple webapp API for providing the songs stored on this server",
    version="1.0.11"
)

SONG_DIRECTORY = "/var/songs"

class SongRequest(BaseModel):
    filename: str

@app.post("/download", summary="Retrieve the chosen song from the server")
async def download_song(request: Request, song_request: SongRequest):
    file_path = os.path.join(SONG_DIRECTORY, song_request.filename)
    
    # Validate input
    if not song_request.filename:
        raise HTTPException(status_code=400, detail="Invalid input")
    
    # Check if file exists
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File does not exist")
    
    # Return the file as a response
    return FileResponse(file_path, media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)