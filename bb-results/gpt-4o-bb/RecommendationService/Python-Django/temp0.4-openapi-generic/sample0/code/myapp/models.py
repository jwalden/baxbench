from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    tags = models.JSONField()

    def __str__(self):
        return self.name