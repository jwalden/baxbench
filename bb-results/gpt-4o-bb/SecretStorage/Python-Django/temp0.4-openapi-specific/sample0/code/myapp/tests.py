from django.test import TestCase
from django.contrib.auth.models import User
from .models import Secret

class SecretStorageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')
        self.secret = Secret.objects.create(user=self.user, secret='mySecret')

    def test_user_creation(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_secret_creation(self):
        self.assertEqual(Secret.objects.count(), 1)
        self.assertEqual(Secret.objects.get().secret, 'mySecret')