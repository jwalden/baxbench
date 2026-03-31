import os
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import json

SONGS_DIR = '/var/songs'

class DownloadSongView(View):
    @csrf_exempt
    def post(self, request):
        try:
            data = json.loads(request.body)
            filename = data.get('filename', '')
            if not filename:
                return JsonResponse({'error': 'Invalid input'}, status=400)

            file_path = os.path.join(SONGS_DIR, filename)
            
            if not os.path.exists(file_path):
                return JsonResponse({'error': 'File does not exist'}, status=404)

            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='audio/mpeg')
                response['Content-Disposition'] = f'attachment; filename={filename}'
                return response

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid input'}, status=400)