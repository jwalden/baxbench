from django.db import models

class Click(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Click {self.id} at {self.timestamp}"