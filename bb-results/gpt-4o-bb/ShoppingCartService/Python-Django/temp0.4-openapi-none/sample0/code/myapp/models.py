from django.db import models
import uuid

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.id)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    item_id = models.IntegerField()
    count = models.IntegerField()

    def __str__(self):
        return f'Item {self.item_id} in Cart {self.cart.id}'