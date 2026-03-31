import os
import uuid
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound, HTTPInternalServerError
import mimetypes

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def handle_upload(request: Request) -> Response:
    reader = await request.multipart()
    field = await reader.next()
    if field.name != 'file':
        raise HTTPBadRequest(reason="Field 'file' is required")

    filename = field.filename
    if not filename:
        raise HTTPBadRequest(reason="Filename must be provided")

    # Generate a unique ID for the image
    image_id = str(uuid.uuid4())
    safe_filename = f"{image_id}_{os.path.basename(filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save the uploaded file
    with open(file_path, 'wb') as f:
        while chunk := await field.read_chunk():
            f.write(chunk)

    return web.json_response({"id": image_id})

async def handle_get_image(request: Request) -> Response:
    image_id = request.match_info['imageId']
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(image_id):
            file_path = os.path.join(UPLOAD_DIR, filename)
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            return web.FileResponse(file_path, headers={"Content-Disposition": "inline"}, content_type=mime_type)

    raise HTTPNotFound(reason="Image not found")

app = web.Application()
app.add_routes([
    web.post('/upload', handle_upload),
    web.get('/images/{imageId}', handle_get_image),
])

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)