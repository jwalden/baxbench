from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('set_secret', views.set_secret, name='set_secret'),
    path('get_secret', views.get_secret, name='get_secret'),
]