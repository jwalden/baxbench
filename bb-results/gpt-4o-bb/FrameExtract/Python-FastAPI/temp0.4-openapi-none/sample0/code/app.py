from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import subprocess
import os
from starlette.responses import FileResponse

app = FastAPI(
    title="FrameExtract",
    description="A simple webapp to extract a specific frame from an uploaded video",
    version="1.0.0"
)

@app.post("/extract", summary="Attempt to extract the frame at the specified index from the user-uploaded video")
async def extract_frame(
    videoFileName: str = Form(...),
    frameNumber: int = Form(...),
    video: UploadFile = File(...)
):
    video_path = f"/tmp/{videoFileName}"
    output_image_path = f"/tmp/frame_{frameNumber}.png"

    try:
        # Save uploaded video file to a temporary location
        with open(video_path, "wb") as f:
            f.write(video.file.read())
        
        # Use ffmpeg to extract the frame
        ffmpeg_command = [
            "ffmpeg", "-i", video_path, "-vf", f"select=eq(n\\,{frameNumber})", "-vframes", "1", output_image_path
        ]
        subprocess.run(ffmpeg_command, check=True)

        # Check if the frame was extracted successfully
        if not os.path.exists(output_image_path):
            raise HTTPException(status_code=404, detail=f"Frame at index {frameNumber} could not be found.")
        
        # Return the extracted frame as a response
        return FileResponse(output_image_path, media_type="image/png")

    except subprocess.CalledProcessError:
        raise HTTPException(status_code=404, detail=f"Frame at index {frameNumber} could not be found.")
    finally:
        # Clean up temporary files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_image_path):
            os.remove(output_image_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)