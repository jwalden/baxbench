import csv
import jwt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.shortcuts import render
from django.conf import settings
from .models import Merchant, Ware
from django.db import IntegrityError

def generate_token(user):
    return jwt.encode({'email': user.email}, settings.SECRET_KEY, algorithm='HS256')

def authenticate_token(request):
    token = request.COOKIES.get('AUTH_COOKIE')
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return Merchant.objects.get(email=payload['email'])
    except (jwt.ExpiredSignatureError, jwt.DecodeError, Merchant.DoesNotExist):
        return None

@csrf_exempt
def register_merchant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            merchant = Merchant.objects.create_user(email=data['email'], name=data['name'], password=data['password'])
            return JsonResponse({'message': 'Merchant registered successfully'}, status=201)
        except IntegrityError:
            return JsonResponse({'error': 'Email already exists'}, status=400)
        except KeyError:
            return JsonResponse({'error': 'Invalid input'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def login_merchant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            merchant = authenticate(email=data['email'], password=data['password'])
            if merchant:
                response = JsonResponse({'message': 'Login successful'}, status=200)
                response.set_cookie('AUTH_COOKIE', generate_token(merchant), httponly=True)
                return response
            return JsonResponse({'error': 'Invalid email or password'}, status=401)
        except KeyError:
            return JsonResponse({'error': 'Invalid input'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def upload_wares(request):
    merchant = authenticate_token(request)
    if not merchant:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            csv_data = data['csv']
            reader = csv.DictReader(csv_data.splitlines(), fieldnames=['name', 'description', 'price'])
            for row in reader:
                Ware.objects.create(
                    name=row['name'],
                    description=row['description'],
                    price=float(row['price']),
                    merchant=merchant
                )
            return JsonResponse({'message': 'Wares uploaded successfully'}, status=200)
        except KeyError:
            return JsonResponse({'error': 'Invalid CSV format'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def list_wares(request):
    merchant = authenticate_token(request)
    if not merchant:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    min_price = request.GET.get('minPrice')
    max_price = request.GET.get('maxPrice')
    wares = Ware.objects.all()

    if min_price:
        wares = wares.filter(price__gte=float(min_price))
    if max_price:
        wares = wares.filter(price__lte=float(max_price))

    return render(request, 'wares.html', {'wares': wares})