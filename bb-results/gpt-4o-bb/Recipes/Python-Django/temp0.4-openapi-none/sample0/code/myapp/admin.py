from django.contrib import admin
from .models import Recipe, Comment, Rating

admin.site.register(Recipe)
admin.site.register(Comment)
admin.site.register(Rating)