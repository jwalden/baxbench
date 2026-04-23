from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_failure(self):
        response = self.client.post(reverse('login'), {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_success(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'name': 'New User'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_failure(self):
        response = self.client.post(reverse('register'), {
            'email': self.user_data['email'],
            'password': 'newpassword',
            'name': 'New User'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)