import aiohttp
from aiohttp import web
import os
import re

# Define the root directory for files
FILES_ROOT = './files'

async def search_files(request):
    try:
        # Extract query parameters
        regex = request.query.get('regex')
        directory = request.query.get('directory', '')
        recursive = request.query.get('recursive', 'false').lower() == 'true'
        
        # Validate regex
        try:
            pattern = re.compile(regex)
        except re.error:
            return web.json_response({'error': 'Malformed regex pattern.'}, status=400)
        
        # Construct the search directory path
        search_dir = os.path.join(FILES_ROOT, directory)
        
        # Validate directory
        if not os.path.exists(search_dir) or not os.path.isdir(search_dir):
            return web.json_response({'error': 'Directory does not exist or is not accessible.'}, status=400)
        
        # List to hold matching files
        matching_files = []

        # Walk through the directory
        for root, _, files in os.walk(search_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern.search(content):
                            # Add the relative path to the list
                            relative_path = os.path.relpath(file_path, start=search_dir)
                            matching_files.append(relative_path)
                except (IOError, UnicodeDecodeError):
                    # Skip files that can't be read
                    continue
            
            # If not recursive, break after the first directory level
            if not recursive:
                break

        return web.json_response({'files': matching_files}, status=200)

    except Exception as e:
        return web.json_response({'error': f'Internal server error: {str(e)}'}, status=500)

app = web.Application()
app.router.add_get('/search', search_files)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)