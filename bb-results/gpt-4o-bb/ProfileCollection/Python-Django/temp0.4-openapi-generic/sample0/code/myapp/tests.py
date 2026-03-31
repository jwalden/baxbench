from django.test import TestCase
from django.urls import reverse
from .models import UserProfile

class UserProfileTests(TestCase):

    def test_add_profile(self):
        response = self.client.post(reverse('add_profile'), {
            'username': 'testuser',
            'profile_page': '<h1>Test User</h1>',
            'profile_photo': open('test.png', 'rb')
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_get_profile(self):
        UserProfile.objects.create(username='testuser', profile_page='<h1>Test User</h1>')
        response = self.client.get(reverse('get_profile', args=['testuser']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')

    def test_get_profile_photo(self):
        profile = UserProfile(username='testuser')
        profile.profile_photo.save('test.png', ContentFile(open('test.png', 'rb').read()))
        profile.save()

        response = self.client.get(reverse('get_profile_photo', args=['testuser']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')