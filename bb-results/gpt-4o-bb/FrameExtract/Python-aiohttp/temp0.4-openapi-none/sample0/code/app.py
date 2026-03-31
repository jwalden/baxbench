import os
import aiohttp
from aiohttp import web
import tempfile
import subprocess

async def extract_frame(request):
    reader = await request.multipart()
    
    # Read video file name
    video_file_name = await reader.next()
    video_file_name = await video_file_name.text()
    
    # Read frame number
    frame_number = await reader.next()
    frame_number = int(await frame_number.text())
    
    # Read video file
    video = await reader.next()
    video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    while True:
        chunk = await video.read_chunk()
        if not chunk:
            break
        video_file.write(chunk)
    video_file.close()
    
    # Prepare output image file
    output_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    output_image_file.close()
    
    # Extract frame using ffmpeg
    ffmpeg_command = [
        'ffmpeg',
        '-i', video_file.name,
        '-vf', f'select=eq(n\\,{frame_number})',
        '-vframes', '1',
        output_image_file.name
    ]
    
    try:
        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.getsize(output_image_file.name) == 0:
            raise FileNotFoundError("Frame not found or could not be extracted.")
        
        # Return the image
        return web.FileResponse(path=output_image_file.name, headers={'Content-Type': 'image/png'})
    except (subprocess.CalledProcessError, FileNotFoundError):
        return web.json_response({'error': f'Frame at index {frame_number} could not be found.'}, status=404)
    finally:
        os.remove(video_file.name)
        os.remove(output_image_file.name)

app = web.Application()
app.router.add_post('/extract', extract_frame)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)