import uuid
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Invitation

@csrf_exempt
def invite_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return JsonResponse({'message': 'Email is required'}, status=400)

        invitation, created = Invitation.objects.get_or_create(email=email)
        if created:
            invitation.invite_id = str(uuid.uuid4())
            invitation.save()

        return JsonResponse({'invite_id': invitation.invite_id, 'message': 'Invitation created'})

@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        invite_id = data.get('invite_id')
        username = data.get('user_name')
        password = data.get('password')

        if not invite_id or not username or not password:
            return JsonResponse({'message': 'All fields are required'}, status=400)

        try:
            invitation = Invitation.objects.get(invite_id=invite_id)
        except Invitation.DoesNotExist:
            return JsonResponse({'message': 'Invalid invite_id'}, status=401)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'message': 'Username already exists. Try providing different username.'}, status=400)

        User.objects.create_user(username=username, password=password)
        invitation.delete()

        return JsonResponse({'message': 'User created'})