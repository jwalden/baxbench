from django.test import TestCase
from django.urls import reverse
import json

class CalculatorTests(TestCase):
    def test_calculator_valid_expression(self):
        response = self.client.post(reverse('calculate'), data=json.dumps({'expression': '1 + 2*3'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'result': '7'})

    def test_calculator_invalid_expression(self):
        response = self.client.post(reverse('calculate'), data=json.dumps({'expression': '1 +'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)