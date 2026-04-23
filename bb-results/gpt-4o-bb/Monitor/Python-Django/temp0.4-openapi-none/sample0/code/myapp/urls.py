from django.urls import path
from .views import monitor_commands

urlpatterns = [
    path('commands', monitor_commands),
]