import asyncio
import json
import re
import subprocess
from aiohttp import web

async def get_running_processes(filter_flags, command_regex):
    try:
        # Run the ps command with the given filter flags
        result = subprocess.run(['ps'] + filter_flags.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            return web.json_response({'code': 500, 'message': 'Failed to retrieve processes'}, status=500)
        
        # Filter the processes based on the command regex
        processes = []
        for line in result.stdout.splitlines()[1:]:  # Skip the header line
            if re.search(command_regex, line):
                parts = line.split(None, 10)  # Split into parts with max 11 parts
                if len(parts) >= 2:
                    process_id = int(parts[1])  # PID is typically the second column
                    processes.append({'processId': process_id, 'processString': line})
        
        return web.json_response(processes)
    except Exception as e:
        return web.json_response({'code': 500, 'message': str(e)}, status=500)

async def handle_monitor_commands(request):
    try:
        data = await request.json()
        filter_flags = data.get('filter_flags', 'aux')  # Default to 'aux' if not provided
        command_regex = data['command_regex']
        
        # Validate command_regex
        try:
            re.compile(command_regex)
        except re.error:
            return web.json_response({'code': 400, 'message': 'Invalid regular expression'}, status=400)
        
        return await get_running_processes(filter_flags, command_regex)
    except json.JSONDecodeError:
        return web.json_response({'code': 400, 'message': 'Invalid JSON'}, status=400)
    except KeyError:
        return web.json_response({'code': 400, 'message': 'Missing required fields'}, status=400)

app = web.Application()
app.router.add_post('/monitor/commands', handle_monitor_commands)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)