from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
import json
from .models import Product

@csrf_exempt
@require_http_methods(["POST"])
def add_product(request):
    try:
        data = json.loads(request.body)
        name = data.pop('name', None)
        if not name:
            return HttpResponseBadRequest("Product name is required.")
        product, created = Product.objects.update_or_create(name=name, defaults={'properties': data})
        return JsonResponse({'message': 'Product successfully added'}, status=201)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")

@require_http_methods(["GET"])
def download_product(request):
    name = request.GET.get('name')
    if not name:
        return HttpResponseBadRequest("Product name is required.")
    product = get_object_or_404(Product, name=name)
    return JsonResponse({'data': json.dumps(product.properties)})

@csrf_exempt
@require_http_methods(["POST"])
def upload_product(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        product_data = data.get('data')
        if not name or not product_data:
            return HttpResponseBadRequest("Name and data are required.")
        product = get_object_or_404(Product, name=name)
        product.properties = json.loads(product_data)
        product.save()
        return JsonResponse({'message': 'Product with the given name was updated.'})
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")

@require_http_methods(["GET"])
def search_products(request):
    query = request.GET.get('query')
    if not query:
        return HttpResponseBadRequest("Search query is required.")
    results = Product.objects.filter(models.Q(name__icontains=query) | models.Q(properties__icontains=query))
    results_data = [{'name': product.name, **product.properties} for product in results]
    return JsonResponse({'results': results_data})