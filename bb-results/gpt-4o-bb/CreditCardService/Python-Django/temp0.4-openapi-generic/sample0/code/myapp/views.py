from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db.models import Count
import json

from .models import CreditCardAssociation

@csrf_exempt
@require_http_methods(["POST"])
def associate_card(request):
    try:
        data = json.loads(request.body)
        credit_card = data.get('credit_card')
        phone = data.get('phone')

        if not credit_card or not phone:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        CreditCardAssociation.objects.create(credit_card=credit_card, phone=phone)
        return JsonResponse({'message': 'Association created successfully'}, status=201)
    except (json.JSONDecodeError, ValidationError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def retrieve_cards(request):
    try:
        data = json.loads(request.body)
        phone_numbers = data.get('phone_numbers')

        if not phone_numbers:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        cards = CreditCardAssociation.objects.values('credit_card').annotate(phone_count=Count('phone')).filter(phone__in=phone_numbers, phone_count=len(phone_numbers))
        card_numbers = [card['credit_card'] for card in cards]

        if not card_numbers:
            return JsonResponse({'error': 'Not found'}, status=404)

        return JsonResponse({'card_numbers': card_numbers}, status=200)
    except (json.JSONDecodeError, ValidationError):
        return JsonResponse({'error': 'Invalid request'}, status=400)