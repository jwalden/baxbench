from django.db import models

class Product(models.Model):
    product_name = models.CharField(max_length=255)
    tags = models.TextField(help_text="Comma-separated tags")

    def __str__(self):
        return self.product_name