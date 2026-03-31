from django.urls import path
from . import views

urlpatterns = [
    path('log', views.log_message, name='log_message'),
    path('logs', views.retrieve_logs, name='retrieve_logs'),
]