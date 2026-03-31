from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
import json

@csrf_exempt
def create_cart(request):
    if request.method == 'POST':
        cart = Cart.objects.create()
        return JsonResponse({'cart_id': str(cart.id)}, status=201)

@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart = get_object_or_404(Cart, id=data['cart_id'])
        item_id = data['item_id']
        count = data['count']

        cart_item, created = CartItem.objects.get_or_create(cart=cart, item_id=item_id)
        cart_item.count += count

        if cart_item.count <= 0:
            cart_item.delete()
        else:
            cart_item.save()

        return JsonResponse({'message': 'Item updated successfully'}, status=200)

@csrf_exempt
def retrieve_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart = get_object_or_404(Cart, id=data['cart_id'])
        items = [{'item_id': item.item_id, 'count': item.count} for item in cart.items.all()]
        return JsonResponse({'items': items}, status=200)