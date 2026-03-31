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
            if not isinstance(message, str):
                return JsonResponse({'error': 'Invalid message format'}, status=400)
            
            with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
                log_file.write(message.replace('\n', ' ') + '\n')
            
            return JsonResponse({'status': 'Log message successful'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def retrieve_logs(request):
    if request.method == 'GET':
        if not os.path.exists(LOG_FILE_PATH):
            return HttpResponse('', content_type='text/plain')
        
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as log_file:
            logs = log_file.read()
        
        return HttpResponse(logs, content_type='text/plain')
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)