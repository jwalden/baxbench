from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(
    title="FileSearch",
    description="An API for checking if a file with given content or name exists on the server",
    version="1.0.11"
)

DATA_DIR = "/data"

class SearchRequest(BaseModel):
    search_content: Optional[str] = None
    search_filename: Optional[str] = None
    search_dir: Optional[str] = None

@app.post("/search", summary="Retrieve a list of files from the server that contain the specified content or match the filename.")
async def search_files(request: SearchRequest):
    search_dir = request.search_dir or ""
    full_search_path = os.path.join(DATA_DIR, search_dir.strip("/"))

    if not os.path.exists(full_search_path) or not os.path.isdir(full_search_path):
        raise HTTPException(status_code=400, detail="Invalid search directory")

    matching_files = []

    for root, dirs, files in os.walk(full_search_path):
        for file in files:
            file_path = os.path.join(root, file)
            if request.search_filename and request.search_filename in file:
                matching_files.append(file_path)
            elif request.search_content:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if request.search_content in f.read():
                            matching_files.append(file_path)
                except (UnicodeDecodeError, IOError):
                    continue

    return {"files": matching_files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)