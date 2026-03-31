from django.test import TestCase
from django.urls import reverse
from .models import Message

class MessageTests(TestCase):
    def test_post_message(self):
        response = self.client.post(reverse('messages'), data={'content': 'Hello, world!', 'username': 'alice'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().content, 'Hello, world!')

    def test_get_messages(self):
        Message.objects.create(content='Hello, world!', username='alice')
        response = self.client.get(reverse('messages'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello, world!')