from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
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
        return HttpResponseBadRequest("Missing 'date' or 'direction' parameter")

    try:
        date = parse_date(date_str)
        if not date:
            raise ValueError("Invalid date format")
    except ValueError:
        return HttpResponseBadRequest("Invalid date format")

    if direction not in ["<", ">", "<=", ">="]:
        return HttpResponseBadRequest("Invalid direction parameter")

    filter_kwargs = {f'timestamp__{direction}': date}
    clicks = Click.objects.filter(**filter_kwargs)

    if not clicks:
        return HttpResponseNotFound("No clicks found")

    click_list = [{'id': click.id, 'timestamp': click.timestamp} for click in clicks]
    return JsonResponse(click_list, safe=False, status=200)