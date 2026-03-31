import os
import aiohttp
from aiohttp import web
import tempfile
import subprocess

routes = web.RouteTableDef()

@routes.post('/extract')
async def extract_frame(request):
    reader = await request.multipart()

    # Read video file name
    video_file_name_field = await reader.next()
    video_file_name = await video_file_name_field.text()

    # Read frame number
    frame_number_field = await reader.next()
    frame_number = int(await frame_number_field.text())

    # Read video file
    video_field = await reader.next()
    video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    video_file_path = video_file.name
    size = 0

    while True:
        chunk = await video_field.read_chunk()
        if not chunk:
            break
        size += len(chunk)
        video_file.write(chunk)

    video_file.close()

    # Prepare output image file path
    output_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    output_image_file_path = output_image_file.name
    output_image_file.close()

    # Use ffmpeg to extract the frame
    try:
        # Calculate the timestamp for the frame
        result = subprocess.run(
            [
                "ffmpeg", "-i", video_file_path, "-vf",
                f"select=eq(n\\,{frame_number})", "-vframes", "1", output_image_file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            return web.json_response({"error": f"Frame at index {frame_number} could not be found."}, status=404)

        # Return the extracted image
        return web.FileResponse(output_image_file_path, headers={'Content-Type': 'image/png'})

    finally:
        # Clean up temporary files
        os.remove(video_file_path)
        if os.path.exists(output_image_file_path):
            os.remove(output_image_file_path)

app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)