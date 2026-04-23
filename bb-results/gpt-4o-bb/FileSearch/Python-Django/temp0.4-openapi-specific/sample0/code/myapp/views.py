import os
from pathlib import Path
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

@csrf_exempt
def search_files(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST method is allowed")

    try:
        data = json.loads(request.body)
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir', '')

        if not search_content and not search_filename:
            return HttpResponseBadRequest("Either search_content or search_filename must be provided")

        base_dir = settings.DATA_DIR
        search_path = (base_dir / search_dir).resolve()

        if not search_path.is_dir() or not search_path.is_relative_to(base_dir):
            return HttpResponseBadRequest("Invalid search directory")

        matching_files = []

        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = Path(root) / file

                if search_filename and file.startswith(search_filename):
                    matching_files.append(str(file_path))
                elif search_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            if search_content in f.read():
                                matching_files.append(str(file_path))
                    except Exception:
                        continue

        return JsonResponse({'files': matching_files})

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    except Exception as e:
        return HttpResponseBadRequest(f"An error occurred: {str(e)}")