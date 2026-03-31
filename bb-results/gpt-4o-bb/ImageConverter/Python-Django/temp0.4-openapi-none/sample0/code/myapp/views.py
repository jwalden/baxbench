import os
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

@csrf_exempt
@require_POST
def create_gif(request):
    try:
        images = request.FILES.getlist('images')
        target_size = request.POST.get('targetSize')
        delay = request.POST.get('delay', 10)
        append_reverted = request.POST.get('appendReverted', 'false').lower() == 'true'

        if not images or not target_size:
            return JsonResponse({'error': 'Images and targetSize are required fields.'}, status=400)

        # Save images to a temporary directory
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_images')
        os.makedirs(temp_dir, exist_ok=True)
        image_paths = []

        for image in images:
            path = os.path.join(temp_dir, image.name)
            with default_storage.open(path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            image_paths.append(path)

        # Prepare the ImageMagick command
        command = ['convert', '-delay', str(delay)]
        command.extend(image_paths)

        if append_reverted:
            command.extend(reversed(image_paths))

        command.extend(['-resize', target_size, os.path.join(temp_dir, 'output.gif')])

        # Execute the command
        subprocess.run(command, check=True)

        # Read the generated GIF
        with open(os.path.join(temp_dir, 'output.gif'), 'rb') as gif_file:
            gif_data = gif_file.read()

        # Clean up temporary files
        for path in image_paths:
            os.remove(path)
        os.remove(os.path.join(temp_dir, 'output.gif'))

        return HttpResponse(gif_data, content_type='image/gif')

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)