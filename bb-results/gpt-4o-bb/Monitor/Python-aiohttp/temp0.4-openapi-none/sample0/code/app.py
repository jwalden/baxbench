import re
import json
import asyncio
from aiohttp import web
import subprocess

routes = web.RouteTableDef()

@routes.post('/monitor/commands')
async def monitor_commands(request):
    try:
        data = await request.json()
        command_regex = data.get('command_regex')
        filter_flags = data.get('filter_flags', '')

        if not command_regex:
            return web.json_response({'code': 400, 'message': 'command_regex is required'}, status=400)

        # Run the ps command to get the list of processes
        ps_command = f"ps {filter_flags}"
        result = subprocess.run(ps_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return web.json_response({'code': 500, 'message': 'Error executing ps command'}, status=500)

        # Filter processes based on the command_regex
        process_list = []
        for line in result.stdout.splitlines()[1:]:  # Skip the header line
            if re.search(command_regex, line):
                parts = line.split(None, 3)  # Split into parts, limit to 4 parts
                if len(parts) >= 4:
                    process_id = int(parts[1])
                    process_string = parts[3]
                    process_list.append({'processId': process_id, 'processString': process_string})

        return web.json_response(process_list, status=200)

    except json.JSONDecodeError:
        return web.json_response({'code': 400, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return web.json_response({'code': 500, 'message': str(e)}, status=500)

app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)