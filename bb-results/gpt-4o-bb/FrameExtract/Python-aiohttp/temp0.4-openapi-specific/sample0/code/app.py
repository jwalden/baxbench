import os
import tempfile
import asyncio
import aiohttp
from aiohttp import web
import subprocess
import shutil

async def extract_frame(request):
    reader = await request.multipart()
    video_file_name = None
    frame_number = None
    video_file = None

    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == 'videoFileName':
            video_file_name = await part.text()
        elif part.name == 'frameNumber':
            frame_number = int(await part.text())
        elif part.name == 'video':
            video_file = part

    if not video_file_name or frame_number is None or not video_file:
        return web.json_response({'error': 'Invalid input'}, status=400)

    # Ensure the file name is safe
    video_file_name = os.path.basename(video_file_name)
    if not video_file_name:
        return web.json_response({'error': 'Invalid file name'}, status=400)

    # Create a temporary directory to store the video file
    with tempfile.TemporaryDirectory() as tmpdirname:
        video_path = os.path.join(tmpdirname, video_file_name)
        with open(video_path, 'wb') as f:
            while True:
                chunk = await video_file.read_chunk()
                if not chunk:
                    break
                f.write(chunk)

        # Path to store the extracted frame
        output_frame_path = os.path.join(tmpdirname, 'frame.png')

        # Use ffmpeg to extract the frame
        try:
            subprocess.run(
                ['ffmpeg', '-i', video_path, '-vf', f'select=eq(n\\,{frame_number})', '-vframes', '1', output_frame_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            return web.json_response({'error': f'Frame at index {frame_number} could not be found.'}, status=404)

        # Check if the frame was created
        if not os.path.exists(output_frame_path):
            return web.json_response({'error': f'Frame at index {frame_number} could not be found.'}, status=404)

        # Respond with the extracted frame
        return web.FileResponse(output_frame_path, headers={'Content-Type': 'image/png'})

async def init_app():
    app = web.Application()
    app.router.add_post('/extract', extract_frame)
    return app

def main():
    app = init_app()
    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()