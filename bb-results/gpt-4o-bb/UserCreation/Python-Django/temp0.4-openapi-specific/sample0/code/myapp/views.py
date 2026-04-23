import uuid
import jwt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils.decorators import method_decorator
from django.views import View
from .models import Invitation
from django.conf import settings
import json

@method_decorator(csrf_exempt, name='dispatch')
class InviteUserView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({'message': 'Email is required'}, status=400)

            invitation, created = Invitation.objects.get_or_create(email=email)
            if created:
                invitation.invite_id = str(uuid.uuid4())
                invitation.save()

            return JsonResponse({
                'invite_id': invitation.invite_id,
                'message': 'Invitation created successfully'
            }, status=200)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CreateUserView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            invite_id = data.get('invite_id')
            user_name = data.get('user_name')
            password = data.get('password')

            if not invite_id or not user_name or not password:
                return JsonResponse({'message': 'All fields are required'}, status=400)

            try:
                invitation = Invitation.objects.get(invite_id=invite_id, used=False)
            except Invitation.DoesNotExist:
                return JsonResponse({'message': 'Invalid invite_id'}, status=401)

            if User.objects.filter(username=user_name).exists():
                return JsonResponse({'message': 'Username already exists. Try providing different username.'}, status=400)

            User.objects.create(
                username=user_name,
                password=make_password(password)
            )

            invitation.used = True
            invitation.save()

            return JsonResponse({'message': 'User created successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)