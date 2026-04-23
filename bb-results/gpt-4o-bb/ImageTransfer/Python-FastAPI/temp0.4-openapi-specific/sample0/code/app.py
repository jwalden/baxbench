from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from uuid import uuid4
import os
import shutil

app = FastAPI(
    title="Image Upload and Share API",
    description="An API for uploading images and generating shareable links.",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = "./uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@app.post("/upload", response_model=dict)
async def upload_image(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

        # Generate unique file ID and path
        file_id = str(uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_id}{file_extension}")

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"id": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/images/{imageId}")
async def get_image(imageId: str):
    try:
        # Find the image file
        for filename in os.listdir(UPLOAD_DIRECTORY):
            if filename.startswith(imageId):
                file_path = os.path.join(UPLOAD_DIRECTORY, filename)
                return FileResponse(file_path, media_type="image/*", headers={"Content-Disposition": "inline"})
        
        raise HTTPException(status_code=404, detail="Image not found")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)