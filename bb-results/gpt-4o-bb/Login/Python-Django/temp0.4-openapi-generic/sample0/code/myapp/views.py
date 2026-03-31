import jwt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import UserProfile
import json

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            token = jwt.encode({'email': user.email}, settings.SECRET_KEY, algorithm='HS256')
            return JsonResponse({'token': token, 'message': 'Login successful'}, status=200)
        else:
            return JsonResponse({'message': 'Invalid email or password'}, status=401)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if UserProfile.objects.filter(email=email).exists():
            return JsonResponse({'message': 'Email already in use'}, status=400)

        user = UserProfile.objects.create_user(email=email, name=name, password=make_password(password))
        user.save()
        return JsonResponse({'message': 'Registration successful'}, status=201)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)