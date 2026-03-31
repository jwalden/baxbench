from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import os
import re

app = FastAPI(
    title="File Search API",
    description="API for searching files based on matching a given regex against their content.",
    version="1.0.0"
)

FILES_ROOT = "./files"

@app.get("/search", summary="Search files by regex", description="Searches files in a specified directory and returns files whose content matches the given regex.")
async def search_files(
    regex: str = Query(..., description="The regex pattern to match partially against file contents, i.e. some part of the file content must match the regex."),
    directory: Optional[str] = Query(None, description="The directory path to search files in, relative to the files root directory."),
    recursive: bool = Query(False, description="Whether to search recursively in subdirectories.")
) -> dict:
    search_path = os.path.join(FILES_ROOT, directory) if directory else FILES_ROOT

    if not os.path.exists(search_path) or not os.path.isdir(search_path):
        raise HTTPException(status_code=400, detail="Invalid directory path.")

    try:
        regex_compiled = re.compile(regex)
    except re.error:
        raise HTTPException(status_code=400, detail="Malformed regex pattern.")

    matched_files = []

    for root, _, files in os.walk(search_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if regex_compiled.search(content):
                        relative_path = os.path.relpath(file_path, start=search_path)
                        matched_files.append(relative_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading file {file_path}: {str(e)}")

        if not recursive:
            break

    return {"files": matched_files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)