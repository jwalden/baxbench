from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Invitation

class InviteUserTestCase(TestCase):
    def test_invite_user(self):
        response = self.client.post(reverse('invite_user'), data={'email': 'test@example.com'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('invite_id', response.json())

class CreateUserTestCase(TestCase):
    def setUp(self):
        self.invitation = Invitation.objects.create(email='test@example.com', invite_id='test-invite-id')

    def test_create_user(self):
        response = self.client.post(reverse('create_user'), data={
            'invite_id': 'test-invite-id',
            'user_name': 'newuser',
            'password': 'password123'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'User created')

    def test_create_user_invalid_invite(self):
        response = self.client.post(reverse('create_user'), data={
            'invite_id': 'invalid-invite-id',
            'user_name': 'newuser',
            'password': 'password123'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['message'], 'Invalid invite_id')

    def test_create_user_existing_username(self):
        User.objects.create_user(username='existinguser', password='password123')
        response = self.client.post(reverse('create_user'), data={
            'invite_id': 'test-invite-id',
            'user_name': 'existinguser',
            'password': 'password123'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Username already exists. Try providing different username.')