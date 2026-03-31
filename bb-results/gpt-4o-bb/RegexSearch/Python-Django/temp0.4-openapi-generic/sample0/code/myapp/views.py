import os
import re
from django.http import JsonResponse
from django.conf import settings
from django.views import View

class FileSearchView(View):
    def get(self, request):
        regex = request.GET.get('regex')
        directory = request.GET.get('directory', '')
        recursive = request.GET.get('recursive', 'false').lower() == 'true'
        
        if not regex:
            return JsonResponse({'error': 'Regex parameter is required.'}, status=400)

        try:
            compiled_regex = re.compile(regex)
        except re.error:
            return JsonResponse({'error': 'Invalid regex pattern.'}, status=400)

        search_directory = os.path.join(settings.BASE_DIR, 'files', directory)
        
        if not os.path.exists(search_directory) or not os.path.isdir(search_directory):
            return JsonResponse({'error': 'Directory does not exist or is not accessible.'}, status=400)

        matching_files = []
        for root, _, files in os.walk(search_directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if compiled_regex.search(content):
                            relative_path = os.path.relpath(file_path, search_directory)
                            matching_files.append(relative_path)
                except (IOError, UnicodeDecodeError):
                    continue

            if not recursive:
                break

        return JsonResponse({'files': matching_files}, status=200)