from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, constr
import os
from pathlib import Path

app = FastAPI(
    title="SongDownloader",
    description="A simple webapp API for providing the songs stored on this server",
    version="1.0.11"
)

# Define the directory where songs are stored
SONG_DIRECTORY = Path("/var/songs")

# Request model
class SongRequest(BaseModel):
    filename: constr(strip_whitespace=True, min_length=1)

@app.post("/download", summary="Retrieve the chosen song from the server")
async def download_song(request: Request, song_request: SongRequest):
    # Ensure the filename is safe and does not contain path traversal characters
    filename = song_request.filename
    if ".." in filename or filename.startswith("/") or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid input")

    # Construct the full path to the song file
    file_path = SONG_DIRECTORY / filename

    # Check if the file exists and is a file
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File does not exist")

    # Return the file as a response
    return FileResponse(file_path, media_type="audio/mpeg")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)