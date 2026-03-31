import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Product

@csrf_exempt
def add_product(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return HttpResponseBadRequest("Name is required.")
            properties = {k: v for k, v in data.items() if k != 'name'}
            product, created = Product.objects.update_or_create(name=name, defaults={'properties': properties})
            return JsonResponse({'message': 'Product successfully added'}, status=201)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON.")
    return HttpResponseBadRequest("Invalid request method.")

def download_product(request):
    if request.method == 'GET':
        name = request.GET.get('name')
        if not name:
            return HttpResponseBadRequest("Name query parameter is required.")
        product = get_object_or_404(Product, name=name)
        return JsonResponse({'data': json.dumps(product.properties)}, status=200)
    return HttpResponseBadRequest("Invalid request method.")

@csrf_exempt
def upload_product(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            product_data = data.get('data')
            if not name or not product_data:
                return HttpResponseBadRequest("Name and data are required.")
            product = get_object_or_404(Product, name=name)
            product.properties = json.loads(product_data)
            product.save()
            return JsonResponse({'message': 'The product with the given name was updated.'}, status=200)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON.")
    return HttpResponseBadRequest("Invalid request method.")

def search_products(request):
    if request.method == 'GET':
        query = request.GET.get('query')
        if not query:
            return HttpResponseBadRequest("Query parameter is required.")
        products = Product.objects.filter(name__icontains=query) | Product.objects.filter(properties__icontains=query)
        results = [{'name': product.name, **product.properties} for product in products]
        return JsonResponse({'results': results}, status=200)
    return HttpResponseBadRequest("Invalid request method.")