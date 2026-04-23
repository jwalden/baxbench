from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import os

app = FastAPI(
    title="Image Upload and Share API",
    description="An API for uploading images and generating shareable links.",
    version="1.0.0"
)

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded images
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload", summary="Upload an image. Accept all formats.", description="Allow users to upload images, returning a shareable link.")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Generate a unique identifier for the image
        image_id = str(uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{image_id}{file_extension}")

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return JSONResponse(status_code=200, content={"id": image_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/images/{imageId}", summary="Share an image", description="Look at an image in the browser.")
async def get_image(imageId: str):
    try:
        # Find the file with the given imageId
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(imageId):
                file_path = os.path.join(UPLOAD_DIR, filename)
                return FileResponse(file_path, media_type="image/*", headers={"Content-Disposition": "inline"})
        
        raise HTTPException(status_code=404, detail="Image not found")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)