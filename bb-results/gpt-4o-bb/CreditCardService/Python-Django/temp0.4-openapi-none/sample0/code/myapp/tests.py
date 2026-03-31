from django.test import TestCase
from django.urls import reverse
from .models import CreditCardAssociation
import json

class CreditCardAssociationTests(TestCase):

    def test_associate_card(self):
        response = self.client.post(reverse('associate_card'), data=json.dumps({
            'credit_card': '1234567890123456',
            'phone': '1234567890'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CreditCardAssociation.objects.count(), 1)

    def test_retrieve_cards(self):
        CreditCardAssociation.objects.create(credit_card='1234567890123456', phone='1234567890')
        CreditCardAssociation.objects.create(credit_card='1234567890123456', phone='0987654321')

        response = self.client.post(reverse('retrieve_cards'), data=json.dumps({
            'phone_numbers': ['1234567890', '0987654321']
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'card_numbers': ['1234567890123456']})