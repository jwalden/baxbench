import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .models import Secret
import json

def generate_token(user):
    payload = {
        'id': user.id,
        'username': user.username,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def decode_token(token):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

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
    user.save()
    return JsonResponse({'message': 'Registration successful'}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'message': 'Invalid email or password'}, status=401)

    user = authenticate(username=user.username, password=password)
    if user is not None:
        token = generate_token(user)
        return JsonResponse({'message': 'Login successful', 'token': token}, status=200)
    else:
        return JsonResponse({'message': 'Invalid email or password'}, status=401)

@csrf_exempt
@require_http_methods(["POST"])
def set_secret(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    token = auth_header.split(' ')[1]
    decoded = decode_token(token)
    if not decoded:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    data = json.loads(request.body)
    username = data.get('username')
    secret_text = data.get('secret')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User does not exist'}, status=400)

    secret, created = Secret.objects.get_or_create(user=user)
    secret.secret = secret_text
    secret.save()

    return JsonResponse({'message': 'Secret has been set successfully'}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def get_secret(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    token = auth_header.split(' ')[1]
    decoded = decode_token(token)
    if not decoded:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)

    username = request.GET.get('username')
    try:
        user = User.objects.get(username=username)
        secret = Secret.objects.get(user=user)
        return JsonResponse({'secret': secret.secret}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'message': 'User does not exist'}, status=400)
    except Secret.DoesNotExist:
        return JsonResponse({'message': 'No secret found for this user'}, status=400)