from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Image
import uuid
import os

@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        image_file = request.FILES.get('file')
        if not image_file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        # Validate the file type
        valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
        if image_file.content_type not in valid_mime_types:
            return JsonResponse({'error': 'Invalid file type'}, status=400)

        image = Image(file=image_file)
        image.save()

        return JsonResponse({'id': str(image.id)}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def view_image(request, image_id):
    image = get_object_or_404(Image, id=image_id)
    image_path = image.file.path
    if not os.path.exists(image_path):
        return JsonResponse({'error': 'File not found'}, status=404)

    with open(image_path, 'rb') as f:
        return HttpResponse(f.read(), content_type=image.file.file.content_type)