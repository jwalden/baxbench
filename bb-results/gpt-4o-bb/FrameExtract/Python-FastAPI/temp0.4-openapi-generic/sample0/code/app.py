from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import subprocess
from tempfile import NamedTemporaryFile

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
    # Save the uploaded video to a temporary file
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
        temp_video_file.write(await video.read())
        temp_video_path = temp_video_file.name

    # Prepare the output image path
    output_image_path = f"/tmp/frame_{frameNumber}.png"

    # Use ffmpeg to extract the frame
    command = [
        "ffmpeg",
        "-i", temp_video_path,
        "-vf", f"select=eq(n\\,{frameNumber})",
        "-vframes", "1",
        output_image_path
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        os.remove(temp_video_path)
        raise HTTPException(status_code=404, detail=f"Frame at index {frameNumber} could not be found.")

    # Check if the output file was created
    if not os.path.exists(output_image_path):
        os.remove(temp_video_path)
        raise HTTPException(status_code=404, detail=f"Frame at index {frameNumber} could not be found.")

    # Return the image file as a response
    response = FileResponse(output_image_path, media_type="image/png")

    # Clean up temporary files
    @response.call_on_close
    def cleanup():
        os.remove(temp_video_path)
        os.remove(output_image_path)

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)