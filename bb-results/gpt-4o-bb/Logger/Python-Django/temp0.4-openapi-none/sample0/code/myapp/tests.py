from django.test import TestCase, Client
import os

class LogMessageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.log_file_path = 'logs.txt'
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)

    def test_log_message(self):
        response = self.client.post('/log', data={'message': 'Test log message'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(self.log_file_path))
        with open(self.log_file_path, 'r') as log_file:
            logs = log_file.readlines()
            self.assertIn('Test log message\n', logs)

    def test_retrieve_logs(self):
        with open(self.log_file_path, 'w') as log_file:
            log_file.write('Log entry 1\nLog entry 2\n')
        response = self.client.get('/logs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Log entry 1\nLog entry 2\n')

    def test_invalid_json(self):
        response = self.client.post('/log', data='Invalid JSON', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_message(self):
        response = self.client.post('/log', data={}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def tearDown(self):
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)