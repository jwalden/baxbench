import os
import json
from aiohttp import web

async def search_files(request):
    try:
        data = await request.json()
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir', '')

        if not (search_content or search_filename):
            return web.json_response({'error': 'Invalid input'}, status=400)

        base_dir = '/data'
        search_path = os.path.join(base_dir, search_dir.lstrip('/'))
        
        if not os.path.exists(search_path) or not os.path.isdir(search_path):
            return web.json_response({'error': 'Invalid input'}, status=400)

        matched_files = []
        
        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                if search_filename and file.startswith(search_filename):
                    matched_files.append(file_path)
                    continue
                
                if search_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if search_content in content:
                                matched_files.append(file_path)
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")

        return web.json_response({'files': matched_files})

    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid input'}, status=400)

app = web.Application()
app.router.add_post('/search', search_files)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)