import os
import aiohttp
from aiohttp import web
import json

# Constants
DATA_DIRECTORY = '/data'
HOST = '0.0.0.0'
PORT = 5000

# Helper function to sanitize directory paths
def sanitize_path(path):
    # Prevent directory traversal attacks
    if '..' in path or path.startswith('/'):
        raise ValueError("Invalid directory path")
    return os.path.normpath(path)

# Function to search files
async def search_files(request):
    try:
        # Parse request
        data = await request.json()
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir', '')

        # Sanitize search directory
        search_dir = sanitize_path(search_dir)
        search_path = os.path.join(DATA_DIRECTORY, search_dir)

        # Validate search path
        if not os.path.exists(search_path):
            return web.json_response({'error': 'Invalid search directory'}, status=400)

        result_files = []

        # Walk through the directory
        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = os.path.join(root, file)

                # Check filename match
                if search_filename and search_filename in file:
                    result_files.append(file_path)

                # Check content match
                if search_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if search_content in content:
                                result_files.append(file_path)
                    except Exception as e:
                        # Handle file read errors
                        print(f"Error reading file {file_path}: {e}")

        return web.json_response({'files': result_files})

    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid JSON input'}, status=400)
    except ValueError as ve:
        return web.json_response({'error': str(ve)}, status=400)
    except Exception as e:
        return web.json_response({'error': f"An unexpected error occurred: {str(e)}"}, status=500)

# Create the app and add routes
app = web.Application()
app.router.add_post('/search', search_files)

# Run the app
if __name__ == '__main__':
    web.run_app(app, host=HOST, port=PORT)