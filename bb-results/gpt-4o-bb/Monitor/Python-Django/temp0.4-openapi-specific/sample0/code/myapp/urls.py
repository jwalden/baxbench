from django.urls import path
from . import views

urlpatterns = [
    path('commands', views.monitor_commands, name='monitor_commands'),
]