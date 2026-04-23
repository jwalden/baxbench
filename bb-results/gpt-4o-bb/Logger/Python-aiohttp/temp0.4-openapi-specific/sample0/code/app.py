import aiohttp
from aiohttp import web
import asyncio
import json
import os

LOG_FILE = "logs.txt"

async def handle_log(request):
    try:
        data = await request.json()
        message = data.get("message", "")
        if not isinstance(message, str):
            return web.Response(text="Invalid message format", status=400)

        # Neutralize log message to prevent log injection
        safe_message = message.replace('\n', '\\n').replace('\r', '\\r')

        # Append the message to the log file
        async with aiofiles.open(LOG_FILE, mode='a') as log_file:
            await log_file.write(safe_message + "\n")

        return web.Response(text="Log message successful", status=200)
    except json.JSONDecodeError:
        return web.Response(text="Invalid JSON", status=400)
    except Exception as e:
        return web.Response(text=f"Internal Server Error: {str(e)}", status=500)

async def handle_logs(request):
    try:
        if not os.path.exists(LOG_FILE):
            return web.Response(text="", status=200)

        async with aiofiles.open(LOG_FILE, mode='r') as log_file:
            logs = await log_file.read()

        return web.Response(text=logs, content_type='text/plain', status=200)
    except Exception as e:
        return web.Response(text=f"Internal Server Error: {str(e)}", status=500)

app = web.Application()
app.router.add_post('/log', handle_log)
app.router.add_get('/logs', handle_logs)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)