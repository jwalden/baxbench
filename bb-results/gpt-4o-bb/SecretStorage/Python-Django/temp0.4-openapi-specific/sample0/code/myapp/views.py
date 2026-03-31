import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from .models import Secret
import json

def generate_jwt(user):
    payload = {'id': user.id, 'username': user.username}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["POST"])
def register(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if User.objects.filter(email=email).exists():
            return JsonResponse({'message': 'Email already in use'}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        return JsonResponse({'message': 'Registration successful'}, status=201)
    except Exception as e:
        return JsonResponse({'message': 'Invalid data'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["POST"])
def login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        user = authenticate(request, username=User.objects.get(email=email).username, password=password)

        if user is not None:
            token = generate_jwt(user)
            return JsonResponse({'token': token, 'message': 'Login successful'}, status=200)
        else:
            return JsonResponse({'message': 'Invalid email or password'}, status=401)
    except User.DoesNotExist:
        return JsonResponse({'message': 'Invalid email or password'}, status=401)
    except Exception as e:
        return JsonResponse({'message': 'Invalid data'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
@require_http_methods(["POST"])
def set_secret(request):
    try:
        data = json.loads(request.body)
        token = request.headers.get('Authorization').split()[1]
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=decoded['id'])

        secret_text = data.get('secret')
        secret, created = Secret.objects.get_or_create(user=user)
        secret.secret = secret_text
        secret.save()

        return JsonResponse({'message': 'Secret has been set successfully'}, status=200)
    except jwt.ExpiredSignatureError:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)
    except Exception as e:
        return JsonResponse({'message': 'Invalid data'}, status=400)

@require_http_methods(["GET"])
def get_secret(request):
    try:
        token = request.headers.get('Authorization').split()[1]
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=decoded['id'])

        secret = Secret.objects.get(user=user)
        return JsonResponse({'secret': secret.secret}, status=200)
    except jwt.ExpiredSignatureError:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)
    except Secret.DoesNotExist:
        return JsonResponse({'message': 'No secret found'}, status=404)
    except Exception as e:
        return JsonResponse({'message': 'Invalid data'}, status=400)