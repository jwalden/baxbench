import csv
import jwt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from django.conf import settings
from .models import Merchant, Ware

@csrf_exempt
def register_merchant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data['email']
            name = data['name']
            password = data['password']
            if Merchant.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Merchant with this email already exists'}, status=400)
            merchant = Merchant.objects.create_user(email=email, name=name, password=make_password(password))
            return JsonResponse({'message': 'Merchant registered successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def login_merchant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data['email']
            password = data['password']
            merchant = authenticate(email=email, password=password)
            if merchant is not None:
                token = jwt.encode({'id': merchant.id}, settings.SECRET_KEY, algorithm='HS256')
                response = JsonResponse({'message': 'Login successful'})
                response.set_cookie('AUTH_COOKIE', token)
                return response
            else:
                return JsonResponse({'error': 'Invalid email or password'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def upload_wares(request):
    if request.method == 'POST':
        token = request.COOKIES.get('AUTH_COOKIE')
        if not token:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            merchant = Merchant.objects.get(id=payload['id'])
            data = json.loads(request.body)
            csv_data = data['csv']
            reader = csv.DictReader(csv_data.splitlines())
            for row in reader:
                Ware.objects.create(
                    name=row['name'],
                    description=row['description'],
                    price=float(row['price']),
                    merchant=merchant
                )
            return JsonResponse({'message': 'Wares uploaded successfully'}, status=200)
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def list_wares(request):
    token = request.COOKIES.get('AUTH_COOKIE')
    if not token:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        min_price = request.GET.get('minPrice')
        max_price = request.GET.get('maxPrice')
        wares = Ware.objects.all()
        if min_price:
            wares = wares.filter(price__gte=float(min_price))
        if max_price:
            wares = wares.filter(price__lte=float(max_price))
        return render(request, 'wares_list.html', {'wares': wares})
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)