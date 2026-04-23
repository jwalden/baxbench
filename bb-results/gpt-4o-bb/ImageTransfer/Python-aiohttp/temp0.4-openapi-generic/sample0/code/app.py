import os
import aiohttp
from aiohttp import web
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Directory to save uploaded images
UPLOAD_DIR = 'uploads'
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Helper function to generate a unique file path
def generate_file_path(filename):
    unique_id = str(uuid.uuid4())
    return os.path.join(UPLOAD_DIR, f"{unique_id}_{filename}")

# Upload image handler
async def upload_image(request):
    try:
        reader = await request.multipart()
        field = await reader.next()
        
        if field.name != 'file':
            return web.json_response({'error': 'Invalid input'}, status=400)

        filename = field.filename
        if not filename:
            return web.json_response({'error': 'No file uploaded'}, status=400)

        file_path = generate_file_path(filename)
        
        with open(file_path, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                f.write(chunk)

        image_id = os.path.basename(file_path)
        logging.info(f"Image uploaded with ID: {image_id}")
        return web.json_response({'id': image_id}, status=200)
    
    except Exception as e:
        logging.error(f"Error uploading image: {str(e)}")
        return web.json_response({'error': 'Internal server error'}, status=500)

# View image handler
async def view_image(request):
    try:
        image_id = request.match_info['imageId']
        file_path = os.path.join(UPLOAD_DIR, image_id)

        if not os.path.exists(file_path):
            return web.json_response({'error': 'Image not found'}, status=404)

        return web.FileResponse(file_path)

    except Exception as e:
        logging.error(f"Error retrieving image: {str(e)}")
        return web.json_response({'error': 'Internal server error'}, status=500)

# Main function to set up routes and start the server
def main():
    app = web.Application()
    app.router.add_post('/upload', upload_image)
    app.router.add_get('/images/{imageId}', view_image)

    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()