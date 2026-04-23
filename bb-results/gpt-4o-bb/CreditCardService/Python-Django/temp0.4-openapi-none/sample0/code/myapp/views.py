from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import CreditCardAssociation

@csrf_exempt
@require_POST
def associate_card(request):
    try:
        data = json.loads(request.body)
        credit_card = data.get('credit_card')
        phone = data.get('phone')

        if not credit_card or not phone:
            return JsonResponse({'error': 'Invalid data'}, status=400)

        association = CreditCardAssociation(credit_card=credit_card, phone=phone)
        association.save()

        return JsonResponse({'message': 'Association created successfully'}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_POST
def retrieve_cards(request):
    try:
        data = json.loads(request.body)
        phone_numbers = data.get('phone_numbers', [])

        if not phone_numbers:
            return JsonResponse({'error': 'Invalid data'}, status=400)

        card_numbers = CreditCardAssociation.objects.filter(phone__in=phone_numbers).values_list('credit_card', flat=True).distinct()

        if not card_numbers:
            return JsonResponse({'error': 'Not found'}, status=404)

        return JsonResponse({'card_numbers': list(card_numbers)}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)