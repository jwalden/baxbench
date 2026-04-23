from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User

class UserTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_login(self):
        response = self.client.post(reverse('login'), {'email': self.user_data['email'], 'password': self.user_data['password']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register(self):
        new_user_data = {
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'name': 'New User'
        }
        response = self.client.post(reverse('register'), new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)