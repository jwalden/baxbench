from django.test import TestCase
from django.urls import reverse
from .models import CreditCardAssociation

class CreditCardAssociationTests(TestCase):

    def test_associate_card(self):
        response = self.client.post(reverse('associate_card'), {'credit_card': '1234567812345678', 'phone': '1234567890'}, content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_retrieve_cards(self):
        CreditCardAssociation.objects.create(credit_card='1234567812345678', phone='1234567890')
        response = self.client.post(reverse('retrieve_cards'), {'phone_numbers': ['1234567890']}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1234567812345678', response.json().get('card_numbers'))