import os
import aiohttp
from aiohttp import web
import tempfile
import shutil
import subprocess

# Constants
UPLOAD_DIR = tempfile.mkdtemp()
CONCATENATED_FILE = os.path.join(UPLOAD_DIR, "concatenated.pdf")

# Helper function to safely concatenate PDFs
async def concatenate_pdfs(file_paths):
    try:
        cmd = ["pdfunite"] + file_paths + [CONCATENATED_FILE]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Failed to concatenate PDF files") from e

# Request handler
async def handle_concatenate(request):
    try:
        reader = await request.multipart()
        file_paths = []

        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "files":
                filename = part.filename
                if not filename.lower().endswith('.pdf'):
                    return web.json_response({'error': 'Invalid file type, only PDF allowed.'}, status=400)
                
                # Securely handle file storage
                with tempfile.NamedTemporaryFile(delete=False, dir=UPLOAD_DIR, suffix=".pdf") as temp_file:
                    file_paths.append(temp_file.name)
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        temp_file.write(chunk)

        if not file_paths:
            return web.json_response({'error': 'Invalid input or missing files.'}, status=400)

        # Concatenate PDFs
        await concatenate_pdfs(file_paths)

        # Send response
        return web.FileResponse(CONCATENATED_FILE, headers={'Content-Type': 'application/pdf'})

    except Exception as e:
        return web.json_response({'error': 'An error occurred while processing the files.'}, status=500)
    finally:
        # Clean up files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except Exception:
                pass

# App setup
app = web.Application()
app.add_routes([web.post('/concatenate', handle_concatenate)])

# Run the app
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)