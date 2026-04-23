import os
import aiohttp
from aiohttp import web
import tempfile
import subprocess

async def convert_pdf_to_text(file_path):
    try:
        # Use pdftotext to convert PDF to text
        with tempfile.NamedTemporaryFile(delete=False) as temp_txt_file:
            temp_txt_path = temp_txt_file.name
        subprocess.run(['pdftotext', file_path, temp_txt_path], check=True)
        with open(temp_txt_path, 'r') as txt_file:
            text_content = txt_file.read()
        os.remove(temp_txt_path)
        return text_content
    except Exception as e:
        raise RuntimeError("Failed to convert PDF to text") from e

async def handle_convert(request):
    reader = await request.multipart()
    field = await reader.next()
    
    if field is None or field.name != 'file':
        return web.json_response({'error': 'Missing file'}, status=400)

    # Save the file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False) as temp_pdf_file:
        temp_pdf_path = temp_pdf_file.name
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            temp_pdf_file.write(chunk)
    
    try:
        # Convert PDF to text
        text_content = await convert_pdf_to_text(temp_pdf_path)
        return web.Response(text=text_content, content_type='text/plain')
    except RuntimeError as e:
        return web.json_response({'error': str(e)}, status=500)
    finally:
        os.remove(temp_pdf_path)

app = web.Application()
app.router.add_post('/convert', handle_convert)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)