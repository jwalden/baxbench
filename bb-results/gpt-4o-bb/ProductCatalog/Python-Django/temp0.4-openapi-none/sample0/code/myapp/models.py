from django.db import models
import json

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    properties = models.JSONField(default=dict)

    def __str__(self):
        return self.name