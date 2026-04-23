from django.test import TestCase
from django.urls import reverse
from .models import Profile
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class ProfileTests(TestCase):

    def setUp(self):
        self.profile_photo = SimpleUploadedFile(name='test_image.png', content=b'\x89PNG\r\n\x1a\n', content_type='image/png')
        self.profile = Profile.objects.create(username='testuser', profile_page='<h1>Test User</h1>', profile_photo=self.profile_photo)

    def test_add_profile(self):
        response = self.client.post(reverse('add_profile'), {
            'username': 'newuser',
            'profile_page': '<h1>New User</h1>',
            'profile_photo': SimpleUploadedFile(name='new_image.png', content=b'\x89PNG\r\n\x1a\n', content_type='image/png')
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Profile.objects.count(), 2)

    def test_get_profile(self):
        response = self.client.get(reverse('get_profile', args=['testuser']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1>Test User</h1>')

    def test_get_profile_photo(self):
        response = self.client.get(reverse('get_profile_photo', args=['testuser']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')