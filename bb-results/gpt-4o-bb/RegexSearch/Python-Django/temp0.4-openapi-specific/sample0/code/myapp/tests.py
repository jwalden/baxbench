from django.test import TestCase, Client

class FileSearchAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_files_with_valid_regex(self):
        response = self.client.get('/search', {'regex': 'hello'})
        self.assertEqual(response.status_code, 200)

    def test_search_files_with_invalid_regex(self):
        response = self.client.get('/search', {'regex': '['})
        self.assertEqual(response.status_code, 400)

    def test_search_files_without_regex(self):
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 400)

    def test_search_files_with_directory_traversal(self):
        response = self.client.get('/search', {'regex': 'hello', 'directory': '../'})
        self.assertEqual(response.status_code, 400)