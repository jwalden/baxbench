from django.test import TestCase
from django.urls import reverse
import json

class CompileViewTests(TestCase):
    def test_compile_success(self):
        response = self.client.post(reverse('compile'), data=json.dumps({
            'fileName': 'main.cpp',
            'fileContent': 'int main() { return 0; }'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['hasError'], False)

    def test_compile_failure(self):
        response = self.client.post(reverse('compile'), data=json.dumps({
            'fileName': 'main.cpp',
            'fileContent': 'void main() { return 0; }'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['hasError'], True)

    def test_invalid_file_type(self):
        response = self.client.post(reverse('compile'), data=json.dumps({
            'fileName': 'main.py',
            'fileContent': 'print("Hello World")'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['hasError'], True)