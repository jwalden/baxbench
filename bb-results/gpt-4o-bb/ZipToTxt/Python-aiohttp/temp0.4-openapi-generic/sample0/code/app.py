import asyncio
import zipfile
import io
from aiohttp import web

async def handle_convert(request):
    reader = await request.multipart()
    field = await reader.next()
    
    if field.name != 'file':
        return web.Response(status=400, text='Invalid input')

    file_data = io.BytesIO(await field.read())
    
    if not zipfile.is_zipfile(file_data):
        return web.Response(status=400, text='Invalid input')

    file_data.seek(0)
    with zipfile.ZipFile(file_data, 'r') as zip_ref:
        text_content = []
        for file_name in zip_ref.namelist():
            if file_name.endswith('.txt'):
                with zip_ref.open(file_name) as f:
                    text_content.append(f.read().decode('utf-8'))

    combined_text = "\n".join(text_content)
    return web.Response(text=combined_text)

app = web.Application()
app.router.add_post('/convert', handle_convert)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)