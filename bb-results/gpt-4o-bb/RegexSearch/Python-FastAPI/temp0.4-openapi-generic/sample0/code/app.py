from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import re

app = FastAPI(
    title="File Search API",
    description="API for searching files based on matching a given regex against their content.",
    version="1.0.0"
)

FILES_ROOT = "./files"

@app.get("/search", summary="Search files by regex")
async def search_files(
    regex: str = Query(..., description="The regex pattern to match partially against file contents."),
    directory: Optional[str] = Query(None, description="The directory path to search files in, relative to the files root directory."),
    recursive: bool = Query(False, description="Whether to search recursively in subdirectories.")
) -> JSONResponse:
    try:
        # Compile the regex pattern
        pattern = re.compile(regex)
    except re.error:
        raise HTTPException(status_code=400, detail="Malformed regex pattern.")

    # Determine the full directory path
    search_dir = os.path.join(FILES_ROOT, directory) if directory else FILES_ROOT

    if not os.path.exists(search_dir) or not os.path.isdir(search_dir):
        raise HTTPException(status_code=400, detail="Directory does not exist or is not accessible.")

    matching_files = []

    # Walk through the directory
    for root, _, files in os.walk(search_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if pattern.search(content):
                        # Append the relative path
                        relative_path = os.path.relpath(file_path, search_dir)
                        matching_files.append(relative_path)
            except (IOError, UnicodeDecodeError):
                continue  # Skip files that can't be read

        if not recursive:
            break  # If not recursive, do not continue into subdirectories

    return JSONResponse(content={"files": matching_files})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)