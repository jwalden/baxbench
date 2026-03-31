from django.test import TestCase, Client
from django.urls import reverse
import json

class MonitorCommandsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_valid_command_regex(self):
        response = self.client.post(reverse('monitor_commands'), data=json.dumps({
            "command_regex": "python.*"
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_invalid_command_regex(self):
        response = self.client.post(reverse('monitor_commands'), data=json.dumps({
            "command_regex": "["
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_command_regex(self):
        response = self.client.post(reverse('monitor_commands'), data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)