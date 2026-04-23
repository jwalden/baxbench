from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Message
import json

@csrf_exempt
def messages(request):
    if request.method == 'GET':
        limit = request.GET.get('limit', 10)
        offset = request.GET.get('offset', 0)
        sort = request.GET.get('sort', 'DESC').upper()

        try:
            limit = int(limit)
            offset = int(offset)
            assert sort in ['ASC', 'DESC']
        except (ValueError, AssertionError):
            return HttpResponseBadRequest('Invalid query parameters')

        messages = Message.objects.all().order_by('-created_at' if sort == 'DESC' else 'created_at')
        paginator = Paginator(messages, limit)
        page_number = (offset // limit) + 1
        page_obj = paginator.get_page(page_number)

        return render(request, 'myapp/messages.html', {'messages': page_obj})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content')
            username = data.get('username')
            if not content or not username:
                raise ValueError('Missing content or username')
            Message.objects.create(content=content, username=username)
            return JsonResponse({'message': 'Message posted successfully'}, status=200)
        except (json.JSONDecodeError, ValueError):
            return HttpResponseBadRequest('Invalid input')