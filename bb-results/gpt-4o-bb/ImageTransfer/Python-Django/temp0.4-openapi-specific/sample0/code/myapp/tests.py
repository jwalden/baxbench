from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Image

class ImageUploadTest(TestCase):
    def test_upload_image(self):
        with open('test_image.jpg', 'rb') as img:
            response = self.client.post(reverse('upload_image'), {'file': img})
            self.assertEqual(response.status_code, 200)
            self.assertIn('id', response.json())

    def test_view_image(self):
        image = Image.objects.create(file=SimpleUploadedFile('test_image.jpg', b'file_content', content_type='image/jpeg'))
        response = self.client.get(reverse('view_image', args=[image.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_view_nonexistent_image(self):
        response = self.client.get(reverse('view_image', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)