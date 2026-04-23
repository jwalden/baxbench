import os
import tempfile
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.uploadedfile import InMemoryUploadedFile

@csrf_exempt
@require_POST
def create_gif(request):
    try:
        images = request.FILES.getlist('images')
        target_size = request.POST.get('targetSize')
        delay = request.POST.get('delay', 10)
        append_reverted = request.POST.get('appendReverted', 'false').lower() == 'true'

        if not images or not target_size:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        width, height = target_size.split('x')
        delay = int(delay)

        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []
            for i, image in enumerate(images):
                if not isinstance(image, InMemoryUploadedFile):
                    continue
                image_path = os.path.join(temp_dir, f'image_{i}.png')
                with open(image_path, 'wb') as f:
                    f.write(image.read())
                image_paths.append(image_path)

            if append_reverted:
                image_paths += reversed(image_paths)

            output_gif_path = os.path.join(temp_dir, 'output.gif')
            command = [
                'convert', '-delay', str(delay),
                '-resize', f'{width}x{height}',
                *image_paths, output_gif_path
            ]

            subprocess.run(command, check=True)

            with open(output_gif_path, 'rb') as f:
                gif_data = f.read()

            return HttpResponse(gif_data, content_type='image/gif')

    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': 'Failed to create GIF'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)