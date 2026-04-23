from django.urls import path
from . import views

urlpatterns = [
    path('log', views.log_message),
    path('logs', views.log_message),
]