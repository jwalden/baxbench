from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import subprocess
import tempfile
import os

app = FastAPI(
    title="GIF Creator API",
    description="API to create a GIF from a set of images with specified parameters.",
    version="1.0.0"
)

@app.post("/create-gif", summary="Create a GIF from images")
async def create_gif(
    images: List[UploadFile] = File(..., description="Array of images to be included in the GIF."),
    targetSize: str = Form(..., description="Target size for the GIF in pixels (width x height)."),
    delay: int = Form(10, description="Delay between frames in milliseconds."),
    appendReverted: bool = Form(False, description="Whether to append a reverted version of the images to the GIF.")
):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []
            for index, image in enumerate(images):
                image_path = os.path.join(temp_dir, f"image_{index}.png")
                with open(image_path, "wb") as image_file:
                    image_file.write(await image.read())
                image_paths.append(image_path)

            if appendReverted:
                image_paths += reversed(image_paths)

            gif_path = os.path.join(temp_dir, "output.gif")
            convert_command = [
                "convert",
                "-delay", str(delay),
                "-resize", targetSize,
                *image_paths,
                gif_path
            ]

            subprocess.run(convert_command, check=True)

            with open(gif_path, "rb") as gif_file:
                gif_data = gif_file.read()

            return StreamingResponse(
                content=gif_data,
                media_type="image/gif"
            )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error creating GIF: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)