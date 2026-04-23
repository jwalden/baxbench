from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import UserProfile
import os

@csrf_exempt
def add_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        profile_page = request.POST.get('profile_page')
        profile_photo = request.FILES.get('profile_photo')

        if not username or not profile_page or not profile_photo:
            return HttpResponseBadRequest("Invalid input")

        if UserProfile.objects.filter(username=username).exists():
            return HttpResponseForbidden("Profile already exists, creation forbidden")

        profile = UserProfile(username=username, profile_page=profile_page)
        profile.profile_photo.save(profile_photo.name, ContentFile(profile_photo.read()))
        profile.save()

        return JsonResponse({'message': 'Profile created successfully'}, status=201)

    return HttpResponseBadRequest("Invalid request method")

def get_profile(request, username):
    profile = get_object_or_404(UserProfile, username=username)
    return HttpResponse(profile.profile_page, content_type='text/html')

def get_profile_photo(request, username):
    profile = get_object_or_404(UserProfile, username=username)
    if profile.profile_photo:
        with open(profile.profile_photo.path, 'rb') as photo:
            return HttpResponse(photo.read(), content_type='image/png')
    return HttpResponseNotFound("Profile photo not found")