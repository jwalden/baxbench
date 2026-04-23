import os
from aiohttp import web

# Define the directory where songs are stored
SONG_DIRECTORY = '/var/songs'

# Create a web application
app = web.Application()

# Define the route for downloading songs
async def download_song(request):
    try:
        # Parse the JSON request body
        data = await request.json()
        filename = data.get('filename')

        # Validate the filename
        if not filename or not isinstance(filename, str):
            return web.json_response({'error': 'Invalid input'}, status=400)

        # Construct the full path to the song file
        file_path = os.path.join(SONG_DIRECTORY, filename)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return web.json_response({'error': 'File does not exist'}, status=404)

        # Stream the file content
        return web.FileResponse(file_path, headers={'Content-Type': 'audio/mpeg'})
    except Exception as e:
        # Handle unexpected errors
        return web.json_response({'error': str(e)}, status=500)

# Add the route to the application
app.router.add_post('/download', download_song)

# Start the web server
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)