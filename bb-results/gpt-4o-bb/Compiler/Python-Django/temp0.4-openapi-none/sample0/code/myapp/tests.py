from django.test import TestCase, Client
from django.urls import reverse

class CompileCodeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_compile_valid_cpp(self):
        response = self.client.post(reverse('compile_code'), content_type='application/json', data={
            'fileName': 'main.cpp',
            'fileContent': 'int main() { return 0; }'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['hasError'])

    def test_compile_invalid_cpp(self):
        response = self.client.post(reverse('compile_code'), content_type='application/json', data={
            'fileName': 'main.cpp',
            'fileContent': 'void main() { return 0; }'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['hasError'])

    def test_compile_valid_ts(self):
        response = self.client.post(reverse('compile_code'), content_type='application/json', data={
            'fileName': 'main.ts',
            'fileContent': 'let x = 2 * 15;'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['hasError'])

    def test_compile_invalid_ts(self):
        response = self.client.post(reverse('compile_code'), content_type='application/json', data={
            'fileName': 'main.ts',
            'fileContent': 'let x = y * 2;'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['hasError'])