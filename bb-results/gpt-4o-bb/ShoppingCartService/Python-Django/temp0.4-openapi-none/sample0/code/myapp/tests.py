from django.test import TestCase
from .models import Cart, CartItem

class CartModelTest(TestCase):
    def test_cart_creation(self):
        cart = Cart.objects.create()
        self.assertIsInstance(cart, Cart)

    def test_cart_item_creation(self):
        cart = Cart.objects.create()
        cart_item = CartItem.objects.create(cart=cart, item_id=1, count=2)
        self.assertIsInstance(cart_item, CartItem)
        self.assertEqual(cart_item.count, 2)