from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from .models import UserProfile
import json

@csrf_exempt
def add_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        profile_page = request.POST.get('profile_page')
        profile_photo = request.FILES.get('profile_photo')

        if not username or not profile_page or not profile_photo:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        if UserProfile.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Profile already exists'}, status=403)

        UserProfile.objects.create(username=username, profile_page=profile_page, profile_photo=profile_photo)
        return JsonResponse({'message': 'Profile created successfully'}, status=201)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_profile(request, username):
    try:
        user_profile = get_object_or_404(UserProfile, username=username)
        return HttpResponse(user_profile.profile_page, content_type='text/html')
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)

def get_profile_photo(request, username):
    try:
        user_profile = get_object_or_404(UserProfile, username=username)
        return HttpResponse(user_profile.profile_photo, content_type='image/png')
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Profile photo not found'}, status=404)