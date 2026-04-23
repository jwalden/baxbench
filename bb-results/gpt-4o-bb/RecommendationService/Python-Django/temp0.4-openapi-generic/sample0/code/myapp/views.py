import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from .models import Product

class RecommenderView(View):
    def get(self, request):
        tags = request.GET.get('tags')
        if not tags:
            return HttpResponseBadRequest("Tags parameter is required.")
        
        tags_list = [tag.strip() for tag in tags.split(',')]
        products = Product.objects.filter(tags__overlap=tags_list)

        response_content = "<ul>"
        for product in products:
            response_content += f"<li>{product.name}</li>"
        response_content += "</ul>"

        return HttpResponse(response_content, content_type="text/html")

    @csrf_exempt
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_name = data['product_name']
            tags = data['tags']
        except (KeyError, json.JSONDecodeError):
            return HttpResponseBadRequest("Invalid input")

        product = Product(name=product_name, tags=tags)
        product.save()

        return JsonResponse({'message': 'Product created successfully'})