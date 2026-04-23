from django.test import TestCase, Client
from django.urls import reverse

class LogMessageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_log_message_post(self):
        response = self.client.post(reverse('log_message'), {'message': 'Test log message'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_log_message_get(self):
        response = self.client.get(reverse('log_message'))
        self.assertEqual(response.status_code, 200)