from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(
    title="FileSearch",
    description="An API for checking if a file with given content or name exists on the server",
    version="1.0.11"
)

class SearchRequest(BaseModel):
    search_content: Optional[str] = None
    search_filename: Optional[str] = None
    search_dir: Optional[str] = None

@app.post("/search", summary="Retrieve a list of files from the server that contain the specified content or match the filename.")
async def search_files(request: SearchRequest):
    base_dir = "/data"
    search_dir = request.search_dir if request.search_dir else ""
    target_dir = os.path.join(base_dir, search_dir.strip("/"))

    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        raise HTTPException(status_code=400, detail="Invalid directory path")

    matching_files = []

    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            if request.search_filename and file.startswith(request.search_filename):
                matching_files.append(file_path)
                continue

            if request.search_content:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        if request.search_content in f.read():
                            matching_files.append(file_path)
                except Exception as e:
                    continue

    return {"files": matching_files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)