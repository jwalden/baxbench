from django.urls import path
from . import views

urlpatterns = [
    path('invite_user', views.invite_user, name='invite_user'),
    path('create_user', views.create_user, name='create_user'),
]