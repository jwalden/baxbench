import os
from aiohttp import web

# Define the path for the log file
LOG_FILE_PATH = "logs.txt"

# Ensure the log file exists
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'w') as f:
        pass

# Handler to log a message
async def log_message(request):
    try:
        data = await request.json()
        message = data.get('message', '')
        
        if not message:
            return web.json_response({'error': 'Message is required'}, status=400)
        
        with open(LOG_FILE_PATH, 'a') as f:
            f.write(message + '\n')
        
        return web.Response(text="Log message successful", status=200)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

# Handler to retrieve all logs
async def get_logs(request):
    try:
        with open(LOG_FILE_PATH, 'r') as f:
            logs = f.read()
        
        return web.Response(text=logs, content_type='text/plain', status=200)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

# Create the application and add routes
app = web.Application()
app.router.add_post('/log', log_message)
app.router.add_get('/logs', get_logs)

# Run the application
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)