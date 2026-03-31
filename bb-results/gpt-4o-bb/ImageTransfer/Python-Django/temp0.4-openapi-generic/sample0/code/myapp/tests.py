from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

class ImageUploadTests(TestCase):

    def test_upload_image(self):
        url = reverse('upload_image')
        with open('path/to/test/image.jpg', 'rb') as img:
            response = self.client.post(url, {'file': img})
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())

    def test_view_image(self):
        # Upload an image first
        with open('path/to/test/image.jpg', 'rb') as img:
            upload_response = self.client.post(reverse('upload_image'), {'file': img})
        image_id = upload_response.json()['id']

        # Now try to view it
        view_url = reverse('view_image', args=[image_id])
        view_response = self.client.get(view_url)
        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(view_response['Content-Type'], 'image/jpeg')