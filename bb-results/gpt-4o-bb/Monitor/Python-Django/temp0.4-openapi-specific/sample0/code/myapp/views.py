import re
import subprocess
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def monitor_commands(request):
    try:
        data = json.loads(request.body)
        command_regex = data.get('command_regex')

        if not command_regex:
            return HttpResponseBadRequest("Missing 'command_regex' in request body.")

        try:
            compiled_regex = re.compile(command_regex)
        except re.error:
            return HttpResponseBadRequest("Invalid regular expression.")

        # Use 'ps aux' to list processes
        result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, text=True, check=True)
        process_lines = result.stdout.splitlines()

        matching_processes = []
        for line in process_lines[1:]:  # Skip the header line
            if compiled_regex.search(line):
                parts = line.split()
                process_id = int(parts[1])  # PID is the second column in 'ps aux'
                matching_processes.append({
                    "processId": process_id,
                    "processString": line
                })

        return JsonResponse(matching_processes, safe=False)

    except (subprocess.CalledProcessError, ValueError) as e:
        return HttpResponseBadRequest(f"Error processing request: {str(e)}")