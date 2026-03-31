from django.test import TestCase, Client
from django.urls import reverse
from .models import Service

class ServiceMonitoringTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.heartbeat_url = reverse('register_heartbeat')
        self.services_url = reverse('get_services')
        self.service_data = {
            'serviceId': 'test-service',
            'token': 'test-token'
        }

    def test_register_heartbeat(self):
        response = self.client.post(self.heartbeat_url, self.service_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.count(), 1)

    def test_get_services(self):
        Service.objects.create(service_id='test-service', token='test-token')
        response = self.client.post(self.services_url, {'token': 'test-token'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)