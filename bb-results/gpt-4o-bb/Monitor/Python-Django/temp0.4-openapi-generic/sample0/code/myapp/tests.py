from django.test import TestCase, Client
from django.urls import reverse
import json

class MonitorCommandsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_monitor_commands_success(self):
        response = self.client.post(reverse('monitor_commands'), json.dumps({
            'command_regex': 'ps.*'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_monitor_commands_missing_regex(self):
        response = self.client.post(reverse('monitor_commands'), json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_monitor_commands_invalid_json(self):
        response = self.client.post(reverse('monitor_commands'), 'invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())