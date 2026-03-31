from django.test import TestCase
from django.urls import reverse
from .models import Product

class RecommenderViewTests(TestCase):
    def setUp(self):
        Product.objects.create(name="Product1", tags=["tag1", "tag2"])
        Product.objects.create(name="Product2", tags=["tag2", "tag3"])

    def test_get_products_by_tags(self):
        response = self.client.get(reverse('recommender'), {'tags': 'tag1'})
        self.assertContains(response, "Product1")
        self.assertNotContains(response, "Product2")

    def test_post_product(self):
        response = self.client.post(reverse('recommender'), 
                                    data=json.dumps({'product_name': 'Product3', 'tags': ['tag1', 'tag4']}), 
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 3)