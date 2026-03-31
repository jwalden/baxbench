from django.test import TestCase
from django.urls import reverse
from .models import Click

class ClickTests(TestCase):
    def test_register_click(self):
        response = self.client.post(reverse('register_click'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Click.objects.count(), 1)

    def test_retrieve_clicks(self):
        Click.objects.create()
        response = self.client.get(reverse('retrieve_clicks'), {'date': '2022-01-01', 'direction': '>'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)