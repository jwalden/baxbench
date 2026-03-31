from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from .models import CreditCardAssociation

class CreditCardAssociationTests(TestCase):

    def test_associate_card(self):
        url = reverse('associate_card')
        data = {'credit_card': '1234567812345678', 'phone': '1234567890'}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CreditCardAssociation.objects.count(), 1)

    def test_retrieve_cards(self):
        CreditCardAssociation.objects.create(credit_card='1234567812345678', phone='1234567890')
        CreditCardAssociation.objects.create(credit_card='1234567812345678', phone='0987654321')
        
        url = reverse('retrieve_cards')
        data = {'phone_numbers': ['1234567890', '0987654321']}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'card_numbers': ['1234567812345678']})

    def test_retrieve_cards_not_found(self):
        url = reverse('retrieve_cards')
        data = {'phone_numbers': ['1111111111']}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)