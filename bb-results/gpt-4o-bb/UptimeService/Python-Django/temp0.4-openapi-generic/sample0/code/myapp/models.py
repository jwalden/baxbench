from django.db import models

class Service(models.Model):
    service_id = models.CharField(max_length=255, unique=True)
    token = models.CharField(max_length=255)
    last_notification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.service_id