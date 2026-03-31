from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
import os
import shutil
import uuid

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
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload", summary="Upload an image. Accept all formats.", description="Allow users to upload images, returning a shareable link.")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Generate a unique ID for the image
        image_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, image_id)

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse(status_code=200, content={"id": image_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/images/{imageId}", summary="Share an image", description="Look at an image in the browser.")
async def get_image(imageId: str):
    try:
        file_path = os.path.join(UPLOAD_DIR, imageId)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")

        # Return the image file as a response
        return FileResponse(file_path, media_type="application/octet-stream", headers={"Content-Disposition": "inline"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)