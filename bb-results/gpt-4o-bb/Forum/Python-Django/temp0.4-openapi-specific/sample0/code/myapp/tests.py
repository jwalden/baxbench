from django.test import TestCase
from django.urls import reverse
from .models import Message

class MessageTests(TestCase):

    def test_post_message(self):
        response = self.client.post(reverse('messages'), {'content': 'Hello World!', 'username': 'alice'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)

    def test_get_messages(self):
        Message.objects.create(content='Hello World!', username='alice')
        response = self.client.get(reverse('messages'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('alice: Hello World!', response.content.decode())