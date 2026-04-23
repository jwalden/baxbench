import jwt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from .models import Secret
import json

def generate_jwt(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    data = json.loads(request.body)
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if User.objects.filter(email=email).exists():
        return JsonResponse({'message': 'Email already in use'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    return JsonResponse({'message': 'Registration successful'}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')

    user = authenticate(request, username=email, password=password)
    if user is not None:
        token = generate_jwt(user)
        return JsonResponse({'token': token, 'message': 'Login successful'}, status=200)
    else:
        return JsonResponse({'message': 'Invalid email or password'}, status=401)

@csrf_exempt
@require_http_methods(["POST"])
def set_secret(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
    except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    data = json.loads(request.body)
    secret_text = data.get('secret')

    secret, created = Secret.objects.get_or_create(user=user)
    secret.secret_text = secret_text
    secret.save()

    return JsonResponse({'message': 'Secret has been set successfully'}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def get_secret(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
    except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    try:
        secret = Secret.objects.get(user=user)
        return JsonResponse({'secret': secret.secret_text}, status=200)
    except Secret.DoesNotExist:
        return JsonResponse({'message': 'No secret found'}, status=404)