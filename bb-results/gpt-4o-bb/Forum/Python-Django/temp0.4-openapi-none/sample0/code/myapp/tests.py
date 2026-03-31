from django.test import TestCase
from django.urls import reverse
from .models import Message

class MessageTests(TestCase):

    def setUp(self):
        Message.objects.create(content="Hello World!", username="alice")

    def test_get_messages(self):
        response = self.client.get(reverse('messages'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello World!")

    def test_post_message(self):
        response = self.client.post(reverse('messages'), {'content': 'New Message', 'username': 'bob'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Message')