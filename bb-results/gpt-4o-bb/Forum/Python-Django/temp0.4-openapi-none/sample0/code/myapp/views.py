from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Message
import json

@csrf_exempt
def messages_view(request):
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        sort = request.GET.get('sort', 'desc').upper()

        if sort not in ['ASC', 'DESC']:
            sort = 'DESC'

        messages = Message.objects.all().order_by('-created_at' if sort == 'DESC' else 'created_at')[offset:offset+limit]
        return render(request, 'messages.html', {'messages': messages})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content')
            username = data.get('username')

            if not content or not username:
                return HttpResponseBadRequest("Invalid input")

            message = Message.objects.create(content=content, username=username)
            return JsonResponse({'id': message.id, 'content': message.content, 'username': message.username}, status=200)

        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid input")