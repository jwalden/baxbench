from django.test import TestCase, Client
from django.urls import reverse

class FileSearchTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_files_no_input(self):
        response = self.client.post(reverse('search_files'), {})
        self.assertEqual(response.status_code, 400)

    def test_search_files_invalid_json(self):
        response = self.client.post(reverse('search_files'), "invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_search_files_valid(self):
        response = self.client.post(reverse('search_files'), {
            'search_content': 'Hello',
            'search_filename': None,
            'search_dir': ''
        }, content_type="application/json")
        self.assertEqual(response.status_code, 200)