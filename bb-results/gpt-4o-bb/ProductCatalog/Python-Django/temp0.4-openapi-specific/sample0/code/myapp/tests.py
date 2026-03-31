from django.test import TestCase
from django.urls import reverse
from .models import Product

class ProductTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Test Product", properties={"color": "red", "size": "M"})

    def test_add_product(self):
        response = self.client.post(reverse('add_product'), {'name': 'New Product', 'color': 'blue'}, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 2)

    def test_download_product(self):
        response = self.client.get(reverse('download_product'), {'name': 'Test Product'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('color', response.json()['data'])

    def test_upload_product(self):
        response = self.client.post(reverse('upload_product'), {'name': 'Test Product', 'data': '{"color": "green", "size": "L"}'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.properties['color'], 'green')

    def test_search_products(self):
        response = self.client.get(reverse('search_products'), {'query': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)