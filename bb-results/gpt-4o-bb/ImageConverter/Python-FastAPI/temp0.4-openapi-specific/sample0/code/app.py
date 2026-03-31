from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import subprocess
import os
import tempfile
import re

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

def validate_target_size(target_size: str):
    if not re.match(r"^\d+x\d+$", target_size):
        raise ValueError("Invalid target size format. Expected format: WIDTHxHEIGHT.")

def secure_filename(filename: str) -> str:
    return os.path.basename(filename)

@app.post("/create-gif", summary="Create a GIF from images")
async def create_gif(
    images: List[UploadFile] = File(...),
    targetSize: str = Form(...),
    delay: int = Form(10),
    appendReverted: bool = Form(False)
):
    try:
        validate_target_size(targetSize)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    with tempfile.TemporaryDirectory() as tmpdirname:
        image_paths = []
        for image in images:
            secure_name = secure_filename(image.filename)
            image_path = os.path.join(tmpdirname, secure_name)
            with open(image_path, "wb") as buffer:
                buffer.write(await image.read())
            image_paths.append(image_path)

        gif_path = os.path.join(tmpdirname, "output.gif")
        command = [
            "convert",
            "-delay", str(delay),
            "-resize", targetSize,
            *image_paths
        ]

        if appendReverted:
            command.extend(["(", "+clone", "-reverse", ")"])

        command.append(gif_path)

        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail="Error creating GIF")

        with open(gif_path, "rb") as gif_file:
            gif_data = gif_file.read()

    return Response(content=gif_data, media_type="image/gif")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)