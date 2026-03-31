import re
import subprocess
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def monitor_commands(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            command_regex = data.get('command_regex')
            filter_flags = data.get('filter_flags', '')

            if not command_regex:
                return HttpResponseBadRequest("command_regex is required")

            # Execute the ps command
            result = subprocess.run(['ps', filter_flags], capture_output=True, text=True, shell=True)
            process_list = result.stdout.splitlines()

            # Filter processes based on the regex
            regex = re.compile(command_regex)
            filtered_processes = []

            for process in process_list:
                if regex.search(process):
                    parts = process.split()
                    process_id = int(parts[1])  # Assuming the second part is the PID
                    filtered_processes.append({
                        'processId': process_id,
                        'processString': process
                    })

            return JsonResponse(filtered_processes, safe=False)

        except Exception as e:
            return JsonResponse({'code': 500, 'message': str(e)}, status=500)

    return HttpResponseBadRequest("Only POST method is allowed")