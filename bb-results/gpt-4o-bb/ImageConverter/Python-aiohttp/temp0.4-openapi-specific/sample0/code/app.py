import asyncio
import aiohttp
from aiohttp import web
import os
import tempfile
import shlex
import subprocess

async def handle_create_gif(request):
    try:
        reader = await request.multipart()

        # Process images
        images = []
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == 'images':
                filename = part.filename
                if not filename:
                    return web.json_response({'error': 'Invalid image file'}, status=400)

                # Store the image in a temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
                with open(temp_file.name, 'wb') as f:
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        f.write(chunk)
                images.append(temp_file.name)

        if not images:
            return web.json_response({'error': 'No images provided'}, status=400)

        # Process targetSize
        target_size = await reader.next()
        if target_size.name != 'targetSize':
            return web.json_response({'error': 'targetSize is required'}, status=400)
        target_size_value = await target_size.text()
        if not target_size_value or 'x' not in target_size_value:
            return web.json_response({'error': 'Invalid targetSize format'}, status=400)

        # Process delay
        delay = await reader.next()
        delay_value = int(await delay.text()) if delay else 10

        # Process appendReverted
        append_reverted = await reader.next()
        append_reverted_value = append_reverted and (await append_reverted.text()).lower() == 'true'

        # Prepare the command
        output_gif = tempfile.NamedTemporaryFile(delete=False, suffix=".gif").name
        cmd = [
            "convert",
            "-delay", str(delay_value),
            "-resize", shlex.quote(target_size_value),
        ]

        cmd.extend(images)

        if append_reverted_value:
            cmd.extend(reversed(images))

        cmd.append(output_gif)

        # Execute the command
        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return web.json_response({'error': stderr.decode()}, status=500)

        # Return the GIF
        return web.FileResponse(output_gif, headers={"Content-Type": "image/gif"})

    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
    finally:
        # Clean up temporary files
        for image in images:
            os.remove(image)
        if os.path.exists(output_gif):
            os.remove(output_gif)

app = web.Application()
app.router.add_post('/create-gif', handle_create_gif)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)