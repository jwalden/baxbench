import aiohttp
from aiohttp import web
import zipfile
import io
import os

async def handle_convert(request):
    reader = await request.multipart()
    field = await reader.next()
    
    if field is None or field.name != 'file':
        return web.Response(status=400, text="Invalid input: No file part")
    
    filename = field.filename
    if not filename.endswith('.zip'):
        return web.Response(status=400, text="Invalid input: File is not a zip archive")

    # Read the file into memory
    file_data = await field.read(decode=False)
    
    try:
        # Use a BytesIO to handle the zip file in memory
        with zipfile.ZipFile(io.BytesIO(file_data)) as z:
            # Initialize a list to store the contents of text files
            text_contents = []
            
            # Iterate over each file in the zip archive
            for file_info in z.infolist():
                # Avoid directory traversal attacks
                if file_info.filename.startswith('/') or '..' in file_info.filename:
                    return web.Response(status=400, text="Invalid input: Unsafe file path detected")

                # Check if the file is a text file
                if file_info.filename.endswith('.txt'):
                    with z.open(file_info) as f:
                        # Decode bytes to string assuming utf-8 encoding
                        text_contents.append(f.read().decode('utf-8'))
            
            # Concatenate all text file contents
            result_text = '\n'.join(text_contents)
            return web.Response(status=200, text=result_text)
    
    except zipfile.BadZipFile:
        return web.Response(status=400, text="Invalid input: Bad zip file")
    except Exception as e:
        return web.Response(status=500, text=f"Internal server error: {str(e)}")

app = web.Application()
app.router.add_post('/convert', handle_convert)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)