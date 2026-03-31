from django.test import TestCase, Client
from django.urls import reverse
import os

class SongDownloaderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.download_url = reverse('download_song')

    def test_download_song_not_found(self):
        response = self.client.post(self.download_url, {'filename': 'non_existent.mp3'}, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_download_song_invalid_input(self):
        response = self.client.post(self.download_url, {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_download_song_invalid_method(self):
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 405)