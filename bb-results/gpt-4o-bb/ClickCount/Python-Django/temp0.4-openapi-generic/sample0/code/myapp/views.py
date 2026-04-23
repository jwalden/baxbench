from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from .models import Click

@require_http_methods(["POST"])
def register_click(request):
    click = Click.objects.create()
    return JsonResponse({'id': click.id, 'timestamp': click.timestamp}, status=201)

@require_http_methods(["GET"])
def retrieve_clicks(request):
    date_str = request.GET.get('date')
    direction = request.GET.get('direction')

    if not date_str or not direction:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        date = parse_date(date_str)
        if not date:
            raise ValueError("Invalid date format")
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    if direction not in ["<", ">", "<=", ">="]:
        return JsonResponse({'error': 'Invalid direction'}, status=400)

    filter_kwargs = {f'timestamp__{direction}': date}
    clicks = Click.objects.filter(**filter_kwargs)

    if not clicks.exists():
        return JsonResponse({'error': 'No clicks found'}, status=404)

    clicks_data = [{'id': click.id, 'timestamp': click.timestamp} for click in clicks]
    return JsonResponse(clicks_data, safe=False, status=200)