import os
import aiohttp
from aiohttp import web

# Constants
SONGS_DIRECTORY = '/var/songs'

# Helper function to validate and sanitize the filename
def sanitize_filename(filename):
    # Prevent path traversal by ensuring the filename does not contain any path separators
    if '..' in filename or os.path.isabs(filename) or '/' in filename or '\\' in filename:
        return None
    return os.path.join(SONGS_DIRECTORY, filename)

# Handler for the /download endpoint
async def download_song(request):
    try:
        # Parse the request JSON
        data = await request.json()
        filename = data.get('filename')

        # Validate input
        if not filename:
            return web.Response(text="Invalid input", status=400)

        # Sanitize and construct the full path
        full_path = sanitize_filename(filename)
        if not full_path:
            return web.Response(text="Invalid input", status=400)

        # Check if the file exists
        if not os.path.isfile(full_path):
            return web.Response(text="File does not exist", status=404)

        # Stream the file content
        return web.FileResponse(full_path, headers={'Content-Type': 'audio/mpeg'})
    except Exception as e:
        # Handle unexpected errors
        return web.Response(text="An unexpected error occurred", status=500)

# Create the application and add routes
app = web.Application()
app.router.add_post('/download', download_song)

# Run the application
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)