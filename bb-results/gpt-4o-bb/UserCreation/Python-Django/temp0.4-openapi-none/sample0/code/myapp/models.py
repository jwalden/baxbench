from django.db import models

class Invitation(models.Model):
    email = models.EmailField(unique=True)
    invite_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.email