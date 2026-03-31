import asyncio
import os
import subprocess
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web import HTTPBadRequest, HTTPInternalServerError
import tempfile

# Constants
HOST = '0.0.0.0'
PORT = 5000

async def create_gif(request: Request) -> Response:
    try:
        # Read and validate the request
        reader = await request.multipart()
        images = []
        target_size = None
        delay = 10
        append_reverted = False

        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == 'images':
                filename = part.filename
                if not filename:
                    raise HTTPBadRequest(reason="Image filename is required.")
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    images.append(temp_file.name)
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        temp_file.write(chunk)
            elif part.name == 'targetSize':
                target_size = await part.text()
            elif part.name == 'delay':
                delay = int(await part.text())
            elif part.name == 'appendReverted':
                append_reverted = (await part.text()).lower() == 'true'

        if not images or not target_size:
            raise HTTPBadRequest(reason="Both images and targetSize are required.")

        # Create GIF
        gif_path = tempfile.mktemp(suffix='.gif')
        try:
            convert_command = [
                'convert',
                '-delay', str(delay),
                '-resize', target_size,
                *images
            ]

            if append_reverted:
                convert_command.extend(reversed(images))

            convert_command.append(gif_path)

            subprocess.run(convert_command, check=True)

            # Return the GIF
            return web.FileResponse(gif_path, headers={'Content-Type': 'image/gif'})

        finally:
            # Clean up temporary files
            for image in images:
                os.unlink(image)
            if os.path.exists(gif_path):
                os.unlink(gif_path)

    except HTTPBadRequest as e:
        return web.json_response({'error': str(e)}, status=400)
    except Exception as e:
        return web.json_response({'error': 'Internal Server Error'}, status=500)

app = web.Application()
app.router.add_post('/create-gif', create_gif)

if __name__ == '__main__':
    web.run_app(app, host=HOST, port=PORT)