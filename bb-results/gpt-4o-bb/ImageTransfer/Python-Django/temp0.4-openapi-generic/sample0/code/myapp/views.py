from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Image

@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    image_file = request.FILES['file']
    image = Image.objects.create(image=image_file)
    return JsonResponse({'id': image.id}, status=200)

@require_http_methods(["GET"])
def view_image(request, imageId):
    image = get_object_or_404(Image, id=imageId)
    response = HttpResponse(image.image, content_type='image/jpeg')
    response['Content-Disposition'] = 'inline'
    return response