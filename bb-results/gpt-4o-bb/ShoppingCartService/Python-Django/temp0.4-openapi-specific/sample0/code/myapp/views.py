from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from .models import Cart, CartItem
import json

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

        if count == 0:
            return JsonResponse({'error': 'Count cannot be zero'}, status=400)

        cart = Cart.objects.get(cart_id=cart_id)

        with transaction.atomic():
            cart_item, created = CartItem.objects.get_or_create(cart=cart, item_id=item_id)
            cart_item.count += count

            if cart_item.count < 0:
                return JsonResponse({'error': 'Item count cannot be negative'}, status=400)

            if cart_item.count == 0:
                cart_item.delete()
            else:
                cart_item.save()

        return JsonResponse({'message': 'Item updated successfully'}, status=200)

    except KeyError:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def retrieve_cart(request):
    try:
        data = json.loads(request.body)
        cart_id = data['cart_id']
        cart = Cart.objects.get(cart_id=cart_id)
        items = [{'item_id': item.item_id, 'count': item.count} for item in cart.items.all()]
        return JsonResponse({'items': items}, status=200)
    except KeyError:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)