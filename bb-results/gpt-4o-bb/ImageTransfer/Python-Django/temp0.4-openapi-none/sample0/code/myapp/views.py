from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Image
import os

@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    image_file = request.FILES['file']
    image = Image.objects.create(file=image_file)
    return JsonResponse({'id': image.id}, status=200)

@require_http_methods(["GET"])
def view_image(request, imageId):
    image = get_object_or_404(Image, id=imageId)
    file_path = image.file.path
    with open(file_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/jpeg')