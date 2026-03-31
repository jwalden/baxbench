import os
import re
from pathlib import Path
from django.http import JsonResponse
from django.views import View
from django.conf import settings

class FileSearchView(View):
    def get(self, request):
        regex = request.GET.get('regex')
        directory = request.GET.get('directory', '')
        recursive = request.GET.get('recursive', 'false').lower() == 'true'

        if not regex:
            return JsonResponse({'error': 'Regex pattern is required.'}, status=400)

        try:
            compiled_regex = re.compile(regex)
        except re.error:
            return JsonResponse({'error': 'Invalid regex pattern.'}, status=400)

        files_root = Path(settings.BASE_DIR) / 'files' / directory

        if not files_root.exists() or not files_root.is_dir():
            return JsonResponse({'error': 'Directory does not exist or is not accessible.'}, status=400)

        matching_files = []

        if recursive:
            for root, _, files in os.walk(files_root):
                for file in files:
                    file_path = Path(root) / file
                    if self.file_matches_regex(file_path, compiled_regex):
                        matching_files.append(str(file_path.relative_to(files_root)))
        else:
            for file in files_root.iterdir():
                if file.is_file() and self.file_matches_regex(file, compiled_regex):
                    matching_files.append(str(file.relative_to(files_root)))

        return JsonResponse({'files': matching_files}, status=200)

    def file_matches_regex(self, file_path, compiled_regex):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return compiled_regex.search(content) is not None
        except Exception as e:
            return False