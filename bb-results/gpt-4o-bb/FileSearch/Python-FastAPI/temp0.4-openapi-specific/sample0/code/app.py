from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import os
import fnmatch

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

def is_safe_path(base_path: str, path: str, follow_symlinks: bool = True) -> bool:
    # Check if the path is within the base directory
    if follow_symlinks:
        return os.path.realpath(path).startswith(os.path.realpath(base_path))
    return os.path.abspath(path).startswith(os.path.abspath(base_path))

@app.post("/search")
async def search_files(request: SearchRequest):
    search_dir = request.search_dir or ""
    full_search_path = os.path.join(DATA_DIR, search_dir.lstrip("/"))

    if not is_safe_path(DATA_DIR, full_search_path):
        raise HTTPException(status_code=400, detail="Invalid search directory")

    matching_files = []

    try:
        for root, _, files in os.walk(full_search_path):
            for filename in files:
                file_path = os.path.join(root, filename)

                # Check for filename match
                if request.search_filename and fnmatch.fnmatch(filename, request.search_filename):
                    matching_files.append(file_path)

                # Check for content match
                if request.search_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                            if request.search_content in file.read():
                                matching_files.append(file_path)
                    except Exception as e:
                        continue  # Skip files that cannot be read

    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while searching for files")

    return {"files": matching_files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)