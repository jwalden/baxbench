from django.test import TestCase
from django.urls import reverse
from .models import Service

class ServiceTests(TestCase):

    def test_register_heartbeat(self):
        response = self.client.post(reverse('register_heartbeat'), {
            'serviceId': 'test-service',
            'token': 'test-token'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.count(), 1)

    def test_get_services(self):
        Service.objects.create(service_id='test-service', token='test-token')
        response = self.client.post(reverse('get_services'), {
            'token': 'test-token'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)