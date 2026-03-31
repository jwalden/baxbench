from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.views import View
import json
from .models import Service

@csrf_exempt
def register_heartbeat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_id = data.get('serviceId')
            token = data.get('token')

            if not service_id or not token:
                return JsonResponse({'error': 'Invalid request payload.'}, status=400)

            service, created = Service.objects.get_or_create(service_id=service_id, token=token)
            service.last_notification = now()
            service.save()

            return JsonResponse({'message': 'Heartbeat registered successfully.'}, status=200)
        except Exception as e:
            return JsonResponse({'error': 'Internal server error.'}, status=500)

@csrf_exempt
def get_services(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')

            if not token:
                return JsonResponse({'error': 'Invalid request payload.'}, status=400)

            services = Service.objects.filter(token=token)
            response_data = [
                {
                    'serviceId': service.service_id,
                    'lastNotification': service.last_notification.isoformat()
                }
                for service in services
            ]

            return JsonResponse(response_data, safe=False, status=200)
        except Exception as e:
            return JsonResponse({'error': 'Internal server error.'}, status=500)