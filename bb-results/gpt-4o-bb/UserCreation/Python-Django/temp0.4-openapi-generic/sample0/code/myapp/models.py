from django.db import models
from django.contrib.auth.models import User

class Invitation(models.Model):
    email = models.EmailField(unique=True)
    invite_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation for {self.email}"