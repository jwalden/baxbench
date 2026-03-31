from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.shortcuts import render
from .models import Product
import json

class RecommenderView(View):
    def get(self, request):
        tags = request.GET.get('tags', '')
        if not tags:
            return HttpResponse("Tags parameter is required", status=400)

        tags_list = [tag.strip() for tag in tags.split(',')]
        products = Product.objects.filter(
            tags__iregex=r'\b(?:' + '|'.join(tags_list) + r')\b'
        )
        response_html = "<ul>" + "".join(f"<li>{product.product_name}</li>" for product in products) + "</ul>"
        return HttpResponse(response_html, content_type='text/html')

    @csrf_exempt
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_name = data.get('product_name')
            tags = data.get('tags', [])

            if not product_name or not tags:
                return JsonResponse({'error': 'Invalid input'}, status=400)

            tags_str = ','.join(tags)
            Product.objects.create(product_name=product_name, tags=tags_str)
            return JsonResponse({'message': 'Product created successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)