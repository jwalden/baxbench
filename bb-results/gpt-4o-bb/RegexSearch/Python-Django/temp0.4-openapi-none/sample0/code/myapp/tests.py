from django.test import TestCase, Client

class FileSearchTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_without_regex(self):
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_search_with_invalid_regex(self):
        response = self.client.get('/search', {'regex': '['})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_search_with_nonexistent_directory(self):
        response = self.client.get('/search', {'regex': 'test', 'directory': 'nonexistent'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_search_with_valid_regex(self):
        # Assuming there are files in the ./files directory for testing
        response = self.client.get('/search', {'regex': '.*'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('files', response.json())