from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import os
import subprocess
import tempfile
from starlette.responses import FileResponse

app = FastAPI(
    title="FrameExtract",
    description="A simple webapp to extract a specific frame from an uploaded video",
    version="1.0.0",
)

@app.post("/extract")
async def extract_frame(
    videoFileName: str = Form(...),
    frameNumber: int = Form(...),
    video: UploadFile = File(...)
):
    # Validate frame number
    if frameNumber < 0:
        raise HTTPException(status_code=400, detail="Frame number must be non-negative.")

    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = os.path.join(temp_dir, "uploaded_video")
        output_image_path = os.path.join(temp_dir, "frame.png")

        # Save the uploaded video to a temporary file
        with open(video_path, "wb") as video_file:
            video_file.write(await video.read())

        # Use ffmpeg to extract the frame
        try:
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"select=eq(n\\,{frameNumber})",
                "-vframes", "1",
                output_image_path
            ]
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=404, detail=f"Frame at index {frameNumber} could not be found.")

        # Check if the frame was extracted
        if not os.path.exists(output_image_path):
            raise HTTPException(status_code=404, detail=f"Frame at index {frameNumber} could not be found.")

        # Return the extracted frame
        return FileResponse(output_image_path, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)