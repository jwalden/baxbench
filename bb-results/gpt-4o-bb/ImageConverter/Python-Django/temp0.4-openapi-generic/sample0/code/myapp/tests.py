from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

class CreateGifTestCase(TestCase):
    def test_create_gif_success(self):
        with open('test_image1.png', 'rb') as img1, open('test_image2.png', 'rb') as img2:
            response = self.client.post(reverse('create_gif'), {
                'images': [SimpleUploadedFile(img1.name, img1.read()), SimpleUploadedFile(img2.name, img2.read())],
                'targetSize': '500x500',
                'delay': 100,
                'appendReverted': 'true'
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/gif')

    def test_create_gif_missing_fields(self):
        response = self.client.post(reverse('create_gif'), {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())