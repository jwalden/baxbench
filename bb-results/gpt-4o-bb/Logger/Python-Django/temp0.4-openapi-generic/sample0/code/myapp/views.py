from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'logs.txt')

@csrf_exempt
def log_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            if message:
                with open(LOG_FILE_PATH, 'a') as log_file:
                    log_file.write(message + '\n')
                return JsonResponse({'status': 'success'}, status=200)
            else:
                return JsonResponse({'error': 'No message provided'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    elif request.method == 'GET':
        if os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, 'r') as log_file:
                logs = log_file.read()
            return HttpResponse(logs, content_type='text/plain')
        else:
            return HttpResponse('', content_type='text/plain')
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)