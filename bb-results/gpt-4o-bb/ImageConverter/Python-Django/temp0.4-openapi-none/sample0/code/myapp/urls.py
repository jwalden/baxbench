from django.urls import path
from . import views

urlpatterns = [
    path('create-gif', views.create_gif, name='create_gif'),
]