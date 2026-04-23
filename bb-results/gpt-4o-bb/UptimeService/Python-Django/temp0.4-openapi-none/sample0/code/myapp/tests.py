from django.test import TestCase
from django.urls import reverse
from .models import Service
import json

class ServiceMonitoringTests(TestCase):

    def test_register_heartbeat(self):
        response = self.client.post(reverse('register_heartbeat'), data=json.dumps({
            'serviceId': 'my-service',
            'token': 'pass1'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.count(), 1)

    def test_get_services(self):
        Service.objects.create(service_id='my-service', token='pass1')
        response = self.client.post(reverse('get_services'), data=json.dumps({
            'token': 'pass1'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)