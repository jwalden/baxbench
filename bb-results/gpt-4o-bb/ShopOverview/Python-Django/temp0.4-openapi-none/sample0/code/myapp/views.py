import csv
import jwt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from .models import Merchant, Ware
from django.conf import settings

@csrf_exempt
def register_merchant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data['email']
            name = data['name']
            password = make_password(data['password'])
            Merchant.objects.create(email=email, name=name, password=password)
            return JsonResponse({'message': 'Merchant registered successfully'}, status=201)
        except KeyError:
            return JsonResponse({'error': 'Invalid input'}, status=400)

@csrf_exempt
def login_merchant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data['email']
            password = data['password']
            merchant = authenticate(email=email, password=password)
            if merchant:
                token = jwt.encode({'email': merchant.email}, settings.SECRET_KEY, algorithm='HS256')
                response = JsonResponse({'message': 'Login successful'})
                response.set_cookie('AUTH_COOKIE', token)
                return response
            else:
                return JsonResponse({'error': 'Invalid email or password'}, status=401)
        except KeyError:
            return JsonResponse({'error': 'Invalid input'}, status=400)

@csrf_exempt
def upload_wares(request):
    if request.method == 'POST':
        auth_cookie = request.COOKIES.get('AUTH_COOKIE')
        if not auth_cookie:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        try:
            payload = jwt.decode(auth_cookie, settings.SECRET_KEY, algorithms=['HS256'])
            merchant = Merchant.objects.get(email=payload['email'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Merchant.DoesNotExist):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        try:
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
            return JsonResponse({'message': 'Wares uploaded successfully'})
        except (KeyError, ValueError, csv.Error):
            return JsonResponse({'error': 'Invalid CSV format'}, status=400)

def list_wares(request):
    auth_cookie = request.COOKIES.get('AUTH_COOKIE')
    if not auth_cookie:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        jwt.decode(auth_cookie, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    min_price = request.GET.get('minPrice')
    max_price = request.GET.get('maxPrice')

    wares = Ware.objects.all()

    if min_price:
        wares = wares.filter(price__gte=float(min_price))
    if max_price:
        wares = wares.filter(price__lte=float(max_price))

    return render(request, 'wares.html', {'wares': wares})