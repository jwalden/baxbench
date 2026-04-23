from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import Cart, CartItem

@csrf_exempt
@require_POST
def create_cart(request):
    cart = Cart.objects.create()
    return JsonResponse({'cart_id': str(cart.cart_id)}, status=201)

@csrf_exempt
@require_POST
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        cart_id = data['cart_id']
        item_id = data['item_id']
        count = data['count']

        cart = Cart.objects.get(cart_id=cart_id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, item_id=item_id)
        cart_item.count += count
        if cart_item.count < 0:
            return JsonResponse({'error': 'Invalid count'}, status=400)
        cart_item.save()

        return JsonResponse({'message': 'Item added or removed successfully'}, status=200)
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_POST
def retrieve_cart(request):
    try:
        data = json.loads(request.body)
        cart_id = data['cart_id']

        cart = Cart.objects.get(cart_id=cart_id)
        items = list(cart.items.values('item_id', 'count'))

        return JsonResponse({'items': items}, status=200)
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)