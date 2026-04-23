import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Invitation
import json

@csrf_exempt
def invite_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if not email:
                return JsonResponse({'message': 'Email is required'}, status=400)

            invitation, created = Invitation.objects.get_or_create(email=email)
            if created:
                invitation.invite_id = str(uuid.uuid4())
                invitation.save()
                message = 'Invitation created'
            else:
                message = 'Invitation already exists'

            return JsonResponse({'invite_id': invitation.invite_id, 'message': message}, status=200)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invite_id = data.get('invite_id')
            user_name = data.get('user_name')
            password = data.get('password')

            if not invite_id or not user_name or not password:
                return JsonResponse({'message': 'All fields are required'}, status=400)

            try:
                invitation = Invitation.objects.get(invite_id=invite_id)
            except Invitation.DoesNotExist:
                return JsonResponse({'message': 'Invalid invite_id'}, status=401)

            if User.objects.filter(username=user_name).exists():
                return JsonResponse({'message': 'Username already exists. Try providing different username.'}, status=400)

            User.objects.create_user(username=user_name, password=password)
            invitation.delete()
            return JsonResponse({'message': 'User created'}, status=200)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)