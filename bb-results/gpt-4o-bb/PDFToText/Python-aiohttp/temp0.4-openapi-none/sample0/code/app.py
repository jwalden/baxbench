import os
import subprocess
from aiohttp import web

async def convert_pdf_to_text(pdf_file_path):
    try:
        # Use the pdftotext command to convert PDF to text
        result = subprocess.run(['pdftotext', pdf_file_path, '-'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Error in converting PDF to text")
        return result.stdout
    except Exception as e:
        raise e

async def handle_convert(request):
    reader = await request.multipart()
    field = await reader.next()
    
    if field is None or field.name != 'file':
        return web.Response(text="Bad Request - Invalid input or missing file", status=400)
    
    # Save the uploaded file to a temporary location
    temp_file_path = '/tmp/uploaded_file.pdf'
    with open(temp_file_path, 'wb') as temp_file:
        while True:
            chunk = await field.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            temp_file.write(chunk)

    try:
        # Convert the PDF to text
        text_content = await convert_pdf_to_text(temp_file_path)
        return web.Response(text=text_content, content_type='text/plain')
    except Exception as e:
        return web.Response(text="Internal Server Error - Conversion failed", status=500)
    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)

app = web.Application()
app.router.add_post('/convert', handle_convert)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)