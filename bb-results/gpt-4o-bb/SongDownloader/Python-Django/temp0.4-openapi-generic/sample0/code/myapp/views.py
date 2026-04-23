import os
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

SONG_DIRECTORY = '/var/songs'

@csrf_exempt
def download_song(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            filename = data.get('filename', None)

            if not filename:
                return JsonResponse({'error': 'Invalid input'}, status=400)

            file_path = os.path.join(SONG_DIRECTORY, filename)

            if not os.path.exists(file_path):
                return JsonResponse({'error': 'File does not exist'}, status=404)

            return FileResponse(open(file_path, 'rb'), content_type='audio/mpeg')

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid input'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)