import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
import json

User = get_user_model()

@csrf_exempt
@require_POST
def login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            token = jwt.encode({'user_id': user.id}, settings.SECRET_KEY, algorithm='HS256')
            return JsonResponse({'token': token, 'message': 'Login successful'}, status=200)
        else:
            return JsonResponse({'message': 'Invalid email or password'}, status=401)
    except Exception as e:
        return JsonResponse({'message': 'An error occurred'}, status=400)

@csrf_exempt
@require_POST
def register(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        if User.objects.filter(email=email).exists():
            return JsonResponse({'message': 'Email already in use'}, status=400)
        user = User.objects.create_user(email=email, password=password, name=name)
        return JsonResponse({'message': 'Registration successful'}, status=201)
    except Exception as e:
        return JsonResponse({'message': 'Invalid data'}, status=400)