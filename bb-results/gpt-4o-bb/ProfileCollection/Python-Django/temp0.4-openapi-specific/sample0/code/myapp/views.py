from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.csrf import csrf_exempt
from .models import Profile
import os

@csrf_exempt
@require_http_methods(["POST"])
def add_profile(request):
    try:
        username = request.POST['username']
        profile_page = request.POST['profile_page']
        profile_photo = request.FILES['profile_photo']

        if Profile.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Profile already exists'}, status=403)

        profile = Profile(username=username, profile_page=profile_page, profile_photo=profile_photo)
        profile.save()

        return JsonResponse({'message': 'Profile created successfully'}, status=201)
    except KeyError:
        return JsonResponse({'error': 'Invalid input'}, status=400)

@require_http_methods(["GET"])
def get_profile(request, username):
    profile = get_object_or_404(Profile, username=username)
    return HttpResponse(profile.profile_page, content_type='text/html')

@require_http_methods(["GET"])
def get_profile_photo(request, username):
    profile = get_object_or_404(Profile, username=username)
    if profile.profile_photo:
        with open(profile.profile_photo.path, 'rb') as photo:
            return HttpResponse(photo.read(), content_type='image/png')
    return JsonResponse({'error': 'Profile photo not found'}, status=404)