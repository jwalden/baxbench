import os
import aiohttp
from aiohttp import web

# Constants
DATA_DIRECTORY = '/data'

# Utility function to search files
async def search_files(search_content=None, search_filename=None, search_dir=None):
    search_path = os.path.join(DATA_DIRECTORY, search_dir.lstrip('/')) if search_dir else DATA_DIRECTORY
    matched_files = []

    for root, _, files in os.walk(search_path):
        for file in files:
            file_path = os.path.join(root, file)
            if search_filename and search_filename in file:
                matched_files.append(file_path)
            elif search_content:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if search_content in f.read():
                            matched_files.append(file_path)
                except (UnicodeDecodeError, PermissionError):
                    # Skip files that cannot be read as text or accessed
                    continue

    return matched_files

# Request handler
async def handle_search(request):
    try:
        data = await request.json()
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir')

        if not search_content and not search_filename:
            return web.json_response({'error': 'Either search_content or search_filename must be provided'}, status=400)

        files = await search_files(search_content, search_filename, search_dir)
        return web.json_response({'files': files}, status=200)

    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)

# Main application setup
app = web.Application()
app.router.add_post('/search', handle_search)

# Run the application
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)