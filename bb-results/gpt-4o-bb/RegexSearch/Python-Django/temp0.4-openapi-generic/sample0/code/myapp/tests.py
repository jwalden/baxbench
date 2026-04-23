from django.test import TestCase, Client

class FileSearchAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_no_regex(self):
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_search_invalid_regex(self):
        response = self.client.get('/search', {'regex': '['})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_search_nonexistent_directory(self):
        response = self.client.get('/search', {'regex': '.*', 'directory': 'nonexistent'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    # Add more tests as needed