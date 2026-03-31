import re
import json
import asyncio
from aiohttp import web
import subprocess

async def handle_monitor_commands(request):
    try:
        data = await request.json()
        command_regex = data.get('command_regex')
        filter_flags = data.get('filter_flags', '')

        if not command_regex:
            return web.json_response({'code': 400, 'message': 'command_regex is required'}, status=400)

        # Compile the regex pattern
        try:
            pattern = re.compile(command_regex)
        except re.error:
            return web.json_response({'code': 400, 'message': 'Invalid regular expression'}, status=400)

        # Prepare the command safely
        ps_command = ['ps'] + filter_flags.split()

        # Execute the command
        try:
            result = subprocess.run(ps_command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return web.json_response({'code': 500, 'message': 'Error executing ps command'}, status=500)

        # Parse the output
        processes = []
        for line in result.stdout.splitlines()[1:]:  # Skip the header line
            if pattern.search(line):
                parts = line.split(None, 10)
                if len(parts) > 1:
                    pid = int(parts[1])
                    processes.append({'processId': pid, 'processString': line})

        return web.json_response(processes, status=200)

    except json.JSONDecodeError:
        return web.json_response({'code': 400, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return web.json_response({'code': 500, 'message': 'Internal Server Error'}, status=500)

app = web.Application()
app.router.add_post('/monitor/commands', handle_monitor_commands)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)