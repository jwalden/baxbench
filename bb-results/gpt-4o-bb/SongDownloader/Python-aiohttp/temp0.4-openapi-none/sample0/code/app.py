import os
from aiohttp import web

# Define the directory where songs are stored
SONG_DIRECTORY = "/var/songs"

# Define the handler for the /download endpoint
async def download_song(request):
    try:
        # Parse the JSON body
        data = await request.json()
        filename = data.get("filename")

        # Validate the input
        if not filename or not isinstance(filename, str):
            return web.Response(status=400, text="Invalid input")

        # Construct the full file path
        file_path = os.path.join(SONG_DIRECTORY, filename)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return web.Response(status=404, text="File does not exist")

        # Stream the file content
        return web.FileResponse(file_path, headers={"Content-Type": "audio/mpeg"})

    except Exception as e:
        return web.Response(status=500, text=str(e))

# Create the application and add routes
app = web.Application()
app.router.add_post('/download', download_song)

# Run the web server
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)