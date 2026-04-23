from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Invitation

class InviteUserTests(TestCase):
    def test_invite_user(self):
        response = self.client.post(reverse('invite_user'), {'email': 'test@example.com'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('invite_id', response.json())

    def test_create_user(self):
        # First, create an invitation
        invitation = Invitation.objects.create(email='test@example.com', invite_id='test-invite-id')

        # Now, create a user using that invitation
        response = self.client.post(reverse('create_user'), {
            'invite_id': 'test-invite-id',
            'user_name': 'testuser',
            'password': 'password123'
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Invitation.objects.count(), 0)