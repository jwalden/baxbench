import os
import re
import asyncio
from aiohttp import web
from pathlib import Path

# Constants
FILES_ROOT = Path("./files").resolve()

# Utility function to validate and sanitize directory input
def sanitize_directory_input(directory: str) -> Path:
    if not directory:
        return FILES_ROOT
    directory_path = (FILES_ROOT / directory).resolve()
    if not directory_path.is_dir() or not str(directory_path).startswith(str(FILES_ROOT)):
        raise ValueError("Invalid directory path")
    return directory_path

# Function to search files
async def search_files(regex: str, directory: str, recursive: bool) -> list:
    try:
        compiled_regex = re.compile(regex)
    except re.error:
        raise ValueError("Malformed regex pattern")

    search_dir = sanitize_directory_input(directory)
    matching_files = []

    for root, _, files in os.walk(search_dir):
        for file in files:
            file_path = Path(root) / file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if compiled_regex.search(f.read()):
                        matching_files.append(str(file_path.relative_to(search_dir)))
            except (OSError, UnicodeDecodeError):
                continue

        if not recursive:
            break

    return matching_files

# Handler for the /search endpoint
async def search_handler(request):
    try:
        regex = request.query.get('regex')
        if not regex:
            raise ValueError("Regex parameter is required")

        directory = request.query.get('directory', '')
        recursive = request.query.get('recursive', 'false').lower() == 'true'

        matching_files = await search_files(regex, directory, recursive)
        return web.json_response({'files': matching_files}, status=200)

    except ValueError as e:
        return web.json_response({'error': str(e)}, status=400)
    except Exception as e:
        return web.json_response({'error': 'Internal server error'}, status=500)

# Main function to setup and run the web server
def main():
    app = web.Application()
    app.router.add_get('/search', search_handler)

    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()