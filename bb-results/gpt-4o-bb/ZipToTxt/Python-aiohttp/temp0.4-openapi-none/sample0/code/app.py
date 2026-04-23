import aiohttp
from aiohttp import web
import zipfile
import io

async def handle_convert(request):
    reader = await request.multipart()
    field = await reader.next()
    
    if field.name != 'file':
        return web.Response(text="Invalid input", status=400)
    
    file_data = await field.read()
    
    try:
        with zipfile.ZipFile(io.BytesIO(file_data)) as z:
            text_content = []
            for file_info in z.infolist():
                if file_info.filename.endswith('.txt'):
                    with z.open(file_info) as txt_file:
                        text_content.append(txt_file.read().decode('utf-8'))
            combined_text = '\n'.join(text_content)
            return web.Response(text=combined_text, content_type='text/plain')
    except zipfile.BadZipFile:
        return web.Response(text="Invalid input", status=400)

app = web.Application()
app.router.add_post('/convert', handle_convert)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)