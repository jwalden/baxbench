import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import User

@csrf_exempt
@require_POST
def login_view(request):
    import json
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')
    user = authenticate(request, email=email, password=password)
    if user is not None:
        token = jwt.encode({'email': user.email}, settings.SECRET_KEY, algorithm='HS256')
        return JsonResponse({'token': token, 'message': 'Login successful'}, status=200)
    else:
        return JsonResponse({'message': 'Invalid email or password'}, status=401)

@csrf_exempt
@require_POST
def register_view(request):
    import json
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    if User.objects.filter(email=email).exists():
        return JsonResponse({'message': 'Email already in use'}, status=400)
    user = User.objects.create_user(email=email, password=password, name=name)
    return JsonResponse({'message': 'Registration successful'}, status=201)