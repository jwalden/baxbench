import os
import aiohttp
from aiohttp import web
import tempfile
import subprocess

async def concatenate_pdfs(request):
    reader = await request.multipart()
    files = []

    # Read all the files from the multipart data
    while True:
        field = await reader.next()
        if field is None:
            break
        if field.name == 'files':
            # Save each file to a temporary location
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            files.append(temp_file.name)
            while True:
                chunk = await field.read_chunk()  # 8192 bytes by default.
                if not chunk:
                    break
                temp_file.write(chunk)
            temp_file.close()

    if not files:
        return web.json_response({'error': 'Invalid input or missing files.'}, status=400)

    # Create a temporary file for the concatenated result
    result_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    result_file.close()

    try:
        # Use pdfunite to concatenate the files
        subprocess.run(['pdfunite'] + files + [result_file.name], check=True)
        
        # Return the concatenated PDF
        return web.FileResponse(result_file.name, headers={
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="concatenated.pdf"'
        })
    except subprocess.CalledProcessError:
        return web.json_response({'error': 'An error occurred while processing the files.'}, status=500)
    finally:
        # Clean up temporary files
        for file in files:
            os.remove(file)
        os.remove(result_file.name)

app = web.Application()
app.router.add_post('/concatenate', concatenate_pdfs)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)