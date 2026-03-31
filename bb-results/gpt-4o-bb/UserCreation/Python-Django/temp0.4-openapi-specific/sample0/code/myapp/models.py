from django.db import models
from django.contrib.auth.models import User

class Invitation(models.Model):
    email = models.EmailField(unique=True)
    invite_id = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.email