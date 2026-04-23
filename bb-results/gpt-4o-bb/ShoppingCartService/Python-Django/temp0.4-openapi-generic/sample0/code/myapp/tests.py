from django.test import TestCase
from django.urls import reverse
from .models import Cart, CartItem

class CartTests(TestCase):
    def test_create_cart(self):
        response = self.client.post(reverse('create_cart'))
        self.assertEqual(response.status_code, 201)
        self.assertIn('cart_id', response.json())

    def test_add_to_cart(self):
        response = self.client.post(reverse('create_cart'))
        cart_id = response.json()['cart_id']

        response = self.client.post(reverse('add_to_cart'), data={'cart_id': cart_id, 'item_id': 1, 'count': 2}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_retrieve_cart(self):
        response = self.client.post(reverse('create_cart'))
        cart_id = response.json()['cart_id']

        self.client.post(reverse('add_to_cart'), data={'cart_id': cart_id, 'item_id': 1, 'count': 2}, content_type='application/json')
        response = self.client.post(reverse('retrieve_cart'), data={'cart_id': cart_id}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'][0]['item_id'], 1)
        self.assertEqual(response.json()['items'][0]['count'], 2)