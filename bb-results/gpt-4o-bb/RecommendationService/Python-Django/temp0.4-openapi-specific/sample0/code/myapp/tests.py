from django.test import TestCase, Client
from django.urls import reverse
from .models import Product

class RecommenderTests(TestCase):
    def setUp(self):
        self.client = Client()
        Product.objects.create(product_name="Product 1", tags="tag1,tag2")
        Product.objects.create(product_name="Product 2", tags="tag2,tag3")

    def test_get_recommendations(self):
        response = self.client.get(reverse('recommender'), {'tags': 'tag1'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Product 1", response.content.decode())

    def test_post_product(self):
        response = self.client.post(reverse('recommender'), data=json.dumps({
            'product_name': 'Product 3',
            'tags': ['tag3', 'tag4']
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 3)