import re
import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def monitor_commands(request):
    try:
        data = json.loads(request.body)
        command_regex = data.get('command_regex')
        filter_flags = data.get('filter_flags', '')

        if not command_regex:
            return JsonResponse({'error': 'command_regex is required'}, status=400)

        # Execute the ps command with the given flags
        result = subprocess.run(['ps'] + filter_flags.split(), capture_output=True, text=True)
        
        if result.returncode != 0:
            return JsonResponse({'error': 'Failed to execute ps command'}, status=500)

        processes = result.stdout.splitlines()
        matching_processes = []

        # Skip the header line
        for process in processes[1:]:
            if re.search(command_regex, process):
                parts = process.split(maxsplit=1)
                if len(parts) > 1:
                    pid, process_string = parts[0], parts[1]
                    matching_processes.append({
                        'processId': int(pid),
                        'processString': process_string
                    })

        return JsonResponse(matching_processes, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)