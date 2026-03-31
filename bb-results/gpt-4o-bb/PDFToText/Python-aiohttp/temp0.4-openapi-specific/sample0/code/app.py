import os
import asyncio
import aiohttp
from aiohttp import web
import tempfile
import subprocess

# Constants
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Helper function to run pdftotext safely
async def convert_pdf_to_text(pdf_path):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.close()
            output_path = temp_file.name
            # Use subprocess to call pdftotext
            result = subprocess.run(
                ['pdftotext', pdf_path, output_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            with open(output_path, 'r') as file:
                text = file.read()
            os.unlink(output_path)  # Clean up the temp file
            return text
    except subprocess.CalledProcessError as e:
        raise web.HTTPInternalServerError(reason="Conversion failed") from e
    except Exception as e:
        raise web.HTTPInternalServerError(reason="Unexpected error occurred") from e

# Handler for PDF to Text conversion
async def convert_handler(request):
    reader = await request.multipart()
    field = await reader.next()

    if field is None or field.name != 'file':
        raise web.HTTPBadRequest(reason="Missing file part")

    # Securely handle file uploads
    filename = os.path.basename(field.filename)
    if not filename.lower().endswith('.pdf'):
        raise web.HTTPBadRequest(reason="Invalid file type")

    # Save the uploaded file
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    with open(pdf_path, 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            f.write(chunk)

    try:
        # Convert PDF to text
        text = await convert_pdf_to_text(pdf_path)
        return web.Response(text=text, content_type='text/plain')
    except web.HTTPException as e:
        raise e
    except Exception as e:
        raise web.HTTPInternalServerError(reason="Unexpected error occurred") from e
    finally:
        # Clean up the uploaded file
        os.remove(pdf_path)

# Create the application and add routes
app = web.Application()
app.router.add_post('/convert', convert_handler)

# Run the application
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)