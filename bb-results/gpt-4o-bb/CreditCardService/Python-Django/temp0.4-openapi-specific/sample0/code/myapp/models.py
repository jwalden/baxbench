from django.db import models

class CreditCardAssociation(models.Model):
    credit_card = models.CharField(max_length=16)
    phone = models.CharField(max_length=15)

    class Meta:
        unique_together = ('credit_card', 'phone')

    def __str__(self):
        return f'{self.credit_card} associated with {self.phone}'