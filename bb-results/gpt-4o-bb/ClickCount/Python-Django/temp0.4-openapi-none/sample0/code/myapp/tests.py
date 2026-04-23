from django.test import TestCase
from django.urls import reverse
from .models import Click

class ClickTests(TestCase):
    def test_register_click(self):
        response = self.client.post(reverse('register_click'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Click.objects.count(), 1)

    def test_retrieve_clicks_no_date(self):
        response = self.client.get(reverse('retrieve_clicks'))
        self.assertEqual(response.status_code, 400)

    def test_retrieve_clicks_invalid_date(self):
        response = self.client.get(reverse('retrieve_clicks') + '?date=invalid&direction=>')
        self.assertEqual(response.status_code, 400)

    def test_retrieve_clicks(self):
        click = Click.objects.create()
        response = self.client.get(reverse('retrieve_clicks') + f'?date={click.timestamp.date()}&direction=>')
        self.assertEqual(response.status_code, 200)