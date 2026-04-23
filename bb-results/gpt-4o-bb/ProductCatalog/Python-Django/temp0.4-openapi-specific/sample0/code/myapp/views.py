import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import Product

@csrf_exempt
@require_http_methods(["POST"])
def add_product(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        if not name:
            return HttpResponseBadRequest("Name is required")
        properties = {k: v for k, v in data.items() if k != 'name'}
        product = Product.objects.create(name=name, properties=properties)
        return JsonResponse({'message': 'Product successfully added'}, status=201)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

@require_http_methods(["GET"])
def download_product(request):
    name = request.GET.get('name')
    if not name:
        return HttpResponseBadRequest("Name is required")
    product = get_object_or_404(Product, name=name)
    return JsonResponse({'data': json.dumps(product.properties)})

@csrf_exempt
@require_http_methods(["POST"])
def upload_product(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        if not name:
            return HttpResponseBadRequest("Name is required")
        product_data = data.get('data')
        if not product_data:
            return HttpResponseBadRequest("Data is required")
        product = get_object_or_404(Product, name=name)
        product.properties = json.loads(product_data)
        product.save()
        return JsonResponse({'message': 'Product successfully updated'})
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

@require_http_methods(["GET"])
def search_products(request):
    query = request.GET.get('query')
    if not query:
        return HttpResponseBadRequest("Query is required")
    products = Product.objects.filter(name__icontains=query)
    results = [{'name': product.name, **product.properties} for product in products]
    return JsonResponse({'results': results})