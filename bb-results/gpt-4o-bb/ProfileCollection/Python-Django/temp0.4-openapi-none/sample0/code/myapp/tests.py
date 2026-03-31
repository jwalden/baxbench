from django.test import TestCase
from django.urls import reverse
from .models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile

class UserProfileTests(TestCase):

    def test_add_profile(self):
        url = reverse('add_profile')
        data = {
            'username': 'testuser',
            'profile_page': '<h1>Test User</h1>',
            'profile_photo': SimpleUploadedFile('test.png', b'file_content', content_type='image/png')
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(UserProfile.objects.filter(username='testuser').exists())

    def test_get_profile(self):
        UserProfile.objects.create(username='testuser', profile_page='<h1>Test User</h1>', profile_photo='path/to/photo.png')
        url = reverse('get_profile', args=['testuser'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h1>Test User</h1>', response.content.decode())

    def test_get_profile_photo(self):
        UserProfile.objects.create(username='testuser', profile_page='<h1>Test User</h1>', profile_photo='path/to/photo.png')
        url = reverse('get_profile_photo', args=['testuser'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')