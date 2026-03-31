from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Secret

class SecretStorageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.client.login(username='test@example.com', password='testpassword')

    def test_register(self):
        response = self.client.post(reverse('register'), data={
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpassword'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_login(self):
        response = self.client.post(reverse('login'), data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())

    def test_set_secret(self):
        response = self.client.post(reverse('login'), data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, content_type='application/json')
        token = response.json().get('token')

        response = self.client.post(reverse('set_secret'), data={
            'secret': 'mySecret'
        }, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)

    def test_get_secret(self):
        Secret.objects.create(user=self.user, secret_text='mySecret')
        response = self.client.post(reverse('login'), data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, content_type='application/json')
        token = response.json().get('token')

        response = self.client.get(reverse('get_secret'), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('secret'), 'mySecret')