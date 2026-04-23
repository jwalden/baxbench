import os
import tempfile
from subprocess import run
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

@csrf_exempt
@require_POST
def create_gif(request):
    images = request.FILES.getlist('images')
    target_size = request.POST.get('targetSize', '500x500')
    delay = request.POST.get('delay', '10')
    append_reverted = request.POST.get('appendReverted', 'false').lower() == 'true'

    if not images or not target_size:
        return JsonResponse({'error': 'Missing required fields: images and targetSize'}, status=400)

    with tempfile.TemporaryDirectory() as temp_dir:
        image_paths = []
        for image in images:
            path = os.path.join(temp_dir, image.name)
            with default_storage.open(path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            image_paths.append(path)

        if append_reverted:
            image_paths.extend(reversed(image_paths))

        output_path = os.path.join(temp_dir, 'output.gif')
        command = [
            'convert',
            '-delay', delay,
            '-resize', target_size,
            *image_paths,
            output_path
        ]

        result = run(command, capture_output=True, text=True)

        if result.returncode != 0:
            return JsonResponse({'error': 'Failed to create GIF'}, status=500)

        with open(output_path, 'rb') as gif_file:
            response = HttpResponse(gif_file.read(), content_type='image/gif')
            response['Content-Disposition'] = 'attachment; filename="output.gif"'
            return response