from django.test import TestCase, Client
from django.urls import reverse
import os

class LogMessageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.log_url = reverse('log_message')
        self.logs_url = reverse('retrieve_logs')
        self.log_file_path = os.path.join(os.path.dirname(__file__), 'logs.txt')

    def tearDown(self):
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)

    def test_log_message(self):
        response = self.client.post(self.log_url, {'message': 'This is a test log message'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(self.log_file_path))
        with open(self.log_file_path, 'r') as f:
            logs = f.read()
        self.assertIn('This is a test log message', logs)

    def test_retrieve_logs(self):
        self.client.post(self.log_url, {'message': 'First log'}, content_type='application/json')
        self.client.post(self.log_url, {'message': 'Second log'}, content_type='application/json')
        response = self.client.get(self.logs_url)
        self.assertEqual(response.status_code, 200)
        logs = response.content.decode('utf-8')
        self.assertIn('First log', logs)
        self.assertIn('Second log', logs)

    def test_invalid_json(self):
        response = self.client.post(self.log_url, 'invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_method(self):
        response = self.client.get(self.log_url)
        self.assertEqual(response.status_code, 405)