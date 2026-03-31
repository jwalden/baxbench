from django.db import models
from django.contrib.auth.models import User

class Secret(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    secret = models.TextField()

    def __str__(self):
        return f'Secret for {self.user.username}'