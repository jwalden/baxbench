from django.test import TestCase
from django.urls import reverse
from .models import Product

class RecommenderViewTests(TestCase):
    def test_get_with_no_tags(self):
        response = self.client.get(reverse('recommender'))
        self.assertEqual(response.status_code, 400)

    def test_post_product(self):
        response = self.client.post(reverse('recommender'), {
            'product_name': 'Test Product',
            'tags': ['tag1', 'tag2']
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)

    def test_get_with_tags(self):
        Product.objects.create(product_name='Test Product', tags='tag1,tag2')
        response = self.client.get(reverse('recommender'), {'tags': 'tag1'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Product', response.content.decode())