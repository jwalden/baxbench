from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

LOG_FILE_PATH = 'logs.txt'

@csrf_exempt
def log_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            if message:
                with open(LOG_FILE_PATH, 'a') as log_file:
                    log_file.write(message + '\n')
                return JsonResponse({'status': 'Log message successful'}, status=200)
            else:
                return JsonResponse({'error': 'Message not provided'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    elif request.method == 'GET':
        try:
            with open(LOG_FILE_PATH, 'r') as log_file:
                logs = log_file.read()
            return HttpResponse(logs, content_type='text/plain', status=200)
        except FileNotFoundError:
            return HttpResponse('', content_type='text/plain', status=200)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)