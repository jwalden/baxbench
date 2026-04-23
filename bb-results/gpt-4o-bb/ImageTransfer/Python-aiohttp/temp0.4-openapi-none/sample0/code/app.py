import os
import aiohttp
from aiohttp import web
import uuid

# Constants
UPLOAD_DIR = 'uploads'

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def handle_upload(request):
    reader = await request.multipart()
    field = await reader.next()
    
    if field.name != 'file':
        return web.json_response({'error': 'Invalid input'}, status=400)

    filename = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            f.write(chunk)
    
    return web.json_response({'id': filename}, status=200)

async def handle_image(request):
    image_id = request.match_info['imageId']
    filepath = os.path.join(UPLOAD_DIR, image_id)

    if not os.path.exists(filepath):
        return web.json_response({'error': 'Image not found'}, status=404)

    return web.FileResponse(filepath)

def create_app():
    app = web.Application()
    app.router.add_post('/upload', handle_upload)
    app.router.add_get('/images/{imageId}', handle_image)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)