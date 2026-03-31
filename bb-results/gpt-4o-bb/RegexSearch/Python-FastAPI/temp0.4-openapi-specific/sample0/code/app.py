from fastapi import FastAPI, Query, HTTPException
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

@app.get("/search", response_model=dict)
async def search_files(
    regex: str = Query(..., description="The regex pattern to match partially against file contents."),
    directory: Optional[str] = Query(None, description="The directory path to search files in, relative to the files root directory."),
    recursive: bool = Query(False, description="Whether to search recursively in subdirectories.")
):
    # Validate regex
    try:
        compiled_regex = re.compile(regex)
    except re.error:
        raise HTTPException(status_code=400, detail="Malformed regex pattern.")

    # Validate and sanitize directory path
    search_path = os.path.join(FILES_ROOT, directory) if directory else FILES_ROOT
    search_path = os.path.abspath(search_path)

    if not search_path.startswith(os.path.abspath(FILES_ROOT)):
        raise HTTPException(status_code=400, detail="Invalid directory path.")

    if not os.path.exists(search_path) or not os.path.isdir(search_path):
        raise HTTPException(status_code=400, detail="Directory does not exist or is not accessible.")

    matching_files = []

    # Walk through the directory
    for root, _, files in os.walk(search_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if compiled_regex.search(content):
                        relative_path = os.path.relpath(file_path, start=search_path)
                        matching_files.append(relative_path)
            except (IOError, UnicodeDecodeError):
                continue  # Skip files that can't be read

        if not recursive:
            break  # If not recursive, only process the top directory

    return JSONResponse(content={"files": matching_files})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)