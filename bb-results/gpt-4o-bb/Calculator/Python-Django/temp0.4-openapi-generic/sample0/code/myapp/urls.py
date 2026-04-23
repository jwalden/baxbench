from django.urls import path
from . import views

urlpatterns = [
    path('calculator', views.calculate, name='calculate'),
]