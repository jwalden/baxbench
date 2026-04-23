from django.urls import path
from . import views

urlpatterns = [
    path('heartbeat', views.register_heartbeat, name='register_heartbeat'),
    path('services', views.get_services, name='get_services'),
]