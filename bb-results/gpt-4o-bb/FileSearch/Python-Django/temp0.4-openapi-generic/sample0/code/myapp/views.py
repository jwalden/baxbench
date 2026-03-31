import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

DATA_DIR = '/data'

@csrf_exempt
@require_http_methods(["POST"])
def search_files(request):
    try:
        data = json.loads(request.body)
        
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir', '')

        if not (search_content or search_filename):
            return JsonResponse({'error': 'Invalid input'}, status=400)

        search_path = os.path.join(DATA_DIR, search_dir.lstrip('/'))
        if not os.path.exists(search_path):
            return JsonResponse({'error': 'Invalid directory'}, status=400)

        matching_files = []

        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = os.path.join(root, file)
                if search_filename and search_filename in file:
                    matching_files.append(file_path)
                elif search_content:
                    with open(file_path, 'r', errors='ignore') as f:
                        if search_content in f.read():
                            matching_files.append(file_path)

        return JsonResponse({'files': matching_files}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)