from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
from starlette.middleware.cors import CORSMiddleware
import zipfile
import os
import io

app = FastAPI(
    title="ZipToTxt",
    description="A simple webapp API for converting zip files into a single text file.",
    version="1.0.11"
)

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert", response_class=PlainTextResponse, summary="Convert a zip file to a text file", description="Convert a zip file into a single text file, concatenating the contents of all text files in the zip.")
async def convert_zip_to_txt(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid input: Only zip files are allowed.")

    try:
        # Read the uploaded file into memory
        file_contents = await file.read()
        with zipfile.ZipFile(io.BytesIO(file_contents)) as zip_file:
            # List of text content from each file
            text_contents = []
            for file_info in zip_file.infolist():
                # Avoid directory traversal attacks
                if not file_info.filename.endswith('.txt') or '..' in file_info.filename or file_info.is_dir():
                    continue
                with zip_file.open(file_info) as f:
                    text_contents.append(f.read().decode('utf-8'))
            
            if not text_contents:
                raise HTTPException(status_code=400, detail="No text files found in the zip.")

            # Concatenate all text contents
            full_text = "\n".join(text_contents)
            return full_text

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid input: The file is not a valid zip file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during file processing: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)