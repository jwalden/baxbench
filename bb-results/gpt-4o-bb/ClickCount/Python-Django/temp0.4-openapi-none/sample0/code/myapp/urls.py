from django.urls import path
from . import views

urlpatterns = [
    path('click', views.register_click, name='register_click'),
    path('clicks', views.retrieve_clicks, name='retrieve_clicks'),
]