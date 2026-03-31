from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import subprocess
import tempfile
import os

app = FastAPI(
    title="GIF Creator API",
    description="API to create a GIF from a set of images with specified parameters.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create-gif", summary="Create a GIF from images")
async def create_gif(
    images: List[UploadFile] = File(..., description="Array of images to be included in the GIF."),
    targetSize: str = Form(..., description="Target size for the GIF in pixels (width x height)."),
    delay: int = Form(10, description="Delay between frames in milliseconds."),
    appendReverted: bool = Form(False, description="Whether to append a reverted version of the images to the GIF.")
):
    try:
        # Validate target size format
        if 'x' not in targetSize:
            raise HTTPException(status_code=400, detail="Invalid target size format. Use 'widthxheight'.")

        # Create a temporary directory to store images
        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []
            for i, image in enumerate(images):
                image_path = os.path.join(temp_dir, f"image_{i}.png")
                with open(image_path, "wb") as f:
                    f.write(await image.read())
                image_paths.append(image_path)

            # Append reverted images if required
            if appendReverted:
                image_paths += reversed(image_paths)

            # Create GIF using ImageMagick
            gif_path = os.path.join(temp_dir, "output.gif")
            convert_command = [
                "convert",
                "-delay", str(delay),
                "-resize", targetSize,
                *image_paths,
                gif_path
            ]
            subprocess.run(convert_command, check=True)

            # Return the GIF
            return StreamingResponse(
                content=open(gif_path, "rb"),
                media_type="image/gif",
                headers={"Content-Disposition": "attachment; filename=output.gif"}
            )
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Failed to create GIF using ImageMagick.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)