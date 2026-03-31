import os
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

@csrf_exempt
def extract_frame(request):
    if request.method == 'POST':
        video_file = request.FILES.get('video')
        frame_number = request.POST.get('frameNumber')

        if not video_file or not frame_number:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        try:
            frame_number = int(frame_number)
        except ValueError:
            return JsonResponse({'error': 'Frame number must be an integer'}, status=400)

        video_path = default_storage.save(video_file.name, ContentFile(video_file.read()))
        video_full_path = os.path.join(settings.MEDIA_ROOT, video_path)

        output_image_path = os.path.join(settings.MEDIA_ROOT, f'frame_{frame_number}.png')

        try:
            command = [
                'ffmpeg',
                '-i', video_full_path,
                '-vf', f'select=eq(n\\,{frame_number})',
                '-vframes', '1',
                output_image_path
            ]
            subprocess.run(command, check=True)

            with open(output_image_path, 'rb') as img_file:
                return HttpResponse(img_file.read(), content_type='image/png')

        except subprocess.CalledProcessError:
            return JsonResponse({'error': f'Frame at index {frame_number} could not be found.'}, status=404)
        finally:
            if os.path.exists(video_full_path):
                os.remove(video_full_path)
            if os.path.exists(output_image_path):
                os.remove(output_image_path)

    return JsonResponse({'error': 'Invalid request method'}, status=405)