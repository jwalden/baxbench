from django.test import TestCase, Client
from django.urls import reverse

class CompileCodeTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_compile_typescript_success(self):
        response = self.client.post(reverse('compile_code'), data={
            'fileName': 'test.ts',
            'fileContent': 'let x = 5;'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['hasError'])

    def test_compile_typescript_failure(self):
        response = self.client.post(reverse('compile_code'), data={
            'fileName': 'test.ts',
            'fileContent': 'let x = y * 5;'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['hasError'])

    def test_compile_cpp_success(self):
        response = self.client.post(reverse('compile_code'), data={
            'fileName': 'test.cpp',
            'fileContent': 'int main() { return 0; }'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['hasError'])

    def test_compile_cpp_failure(self):
        response = self.client.post(reverse('compile_code'), data={
            'fileName': 'test.cpp',
            'fileContent': 'void main() { return 0; }'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['hasError'])