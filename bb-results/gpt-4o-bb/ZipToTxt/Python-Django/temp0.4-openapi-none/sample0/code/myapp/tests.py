from django.test import TestCase, Client
from django.urls import reverse
import zipfile
import io

class ConvertZipToTxtTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_convert_zip_to_txt(self):
        # Create a zip file in memory
        in_memory_zip = io.BytesIO()
        with zipfile.ZipFile(in_memory_zip, 'w') as zf:
            zf.writestr('file1.txt', 'Hello')
            zf.writestr('file2.txt', 'World')
        
        in_memory_zip.seek(0)

        response = self.client.post(reverse('convert_zip_to_txt'), {'file': in_memory_zip}, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello', response.content.decode())
        self.assertIn('World', response.content.decode())

    def test_invalid_file_format(self):
        response = self.client.post(reverse('convert_zip_to_txt'), {'file': io.BytesIO(b'Not a zip file')}, format='multipart')
        self.assertEqual(response.status_code, 400)