from django.urls import path
from . import views

urlpatterns = [
    path('create_cart', views.create_cart, name='create_cart'),
    path('add_to_cart', views.add_to_cart, name='add_to_cart'),
    path('retrieve_cart', views.retrieve_cart, name='retrieve_cart'),
]