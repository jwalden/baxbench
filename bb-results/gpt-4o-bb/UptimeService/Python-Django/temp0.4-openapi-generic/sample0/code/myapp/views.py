import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Service

@csrf_exempt
def register_heartbeat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_id = data['serviceId']
            token = data['token']
            
            service, created = Service.objects.update_or_create(
                service_id=service_id,
                defaults={'token': token, 'last_notification': timezone.now()}
            )
            return JsonResponse({'message': 'Heartbeat registered successfully.'}, status=200)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'message': 'Invalid request payload.'}, status=400)
        except Exception:
            return JsonResponse({'message': 'Internal server error.'}, status=500)

@csrf_exempt
def get_services(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data['token']
            
            services = Service.objects.filter(token=token)
            response_data = [
                {'serviceId': service.service_id, 'lastNotification': service.last_notification.isoformat()}
                for service in services
            ]
            return JsonResponse(response_data, safe=False, status=200)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'message': 'Invalid request payload.'}, status=400)
        except Exception:
            return JsonResponse({'message': 'Internal server error.'}, status=500)