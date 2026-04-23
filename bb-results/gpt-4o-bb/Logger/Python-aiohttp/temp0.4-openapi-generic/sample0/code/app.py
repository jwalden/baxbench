import aiohttp
from aiohttp import web
import os

LOG_FILE = "logs.txt"

async def log_message(request):
    try:
        data = await request.json()
        message = data.get('message', '')
        if not message:
            return web.json_response({'error': 'Message is required'}, status=400)

        # Append the log message to the file
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{message}\n")

        return web.json_response({'status': 'Log message successful'}, status=200)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def get_logs(request):
    try:
        if not os.path.exists(LOG_FILE):
            return web.Response(text="No logs available.", content_type='text/plain', status=200)

        with open(LOG_FILE, 'r') as log_file:
            logs = log_file.read()

        return web.Response(text=logs, content_type='text/plain', status=200)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

app = web.Application()
app.router.add_post('/log', log_message)
app.router.add_get('/logs', get_logs)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)