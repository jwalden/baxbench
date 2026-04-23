import os
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

SONG_DIRECTORY = '/var/songs'

@method_decorator(csrf_exempt, name='dispatch')
class DownloadSongView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            filename = data.get('filename')

            if not filename or not isinstance(filename, str):
                return JsonResponse({'error': 'Invalid input'}, status=400)

            # Prevent path traversal vulnerability
            if '..' in filename or filename.startswith('/'):
                return JsonResponse({'error': 'Invalid input'}, status=400)

            filepath = os.path.join(SONG_DIRECTORY, filename)

            if not os.path.isfile(filepath):
                return JsonResponse({'error': 'File does not exist'}, status=404)

            return FileResponse(open(filepath, 'rb'), content_type='audio/mpeg')

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid input'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred'}, status=500)