from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from .models import Product
import json

@require_http_methods(["GET", "POST"])
def recommender(request):
    if request.method == "GET":
        tags = request.GET.get('tags', '')
        if not tags:
            return HttpResponseBadRequest("Tags parameter is required.")
        
        tags_set = set(tag.strip() for tag in tags.split(','))
        products = Product.objects.all()
        matching_products = [product for product in products if tags_set.intersection(product.get_tags_list())]

        response_content = "<ul>"
        for product in matching_products:
            response_content += f"<li>{product.product_name}</li>"
        response_content += "</ul>"

        return HttpResponse(response_content, content_type="text/html")

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            product_name = data.get('product_name', '')
            tags = data.get('tags', [])
            if not product_name or not isinstance(tags, list):
                return HttpResponseBadRequest("Invalid input")

            Product.objects.create(product_name=product_name, tags=','.join(tags))
            return JsonResponse({"message": "Product added successfully"})
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")