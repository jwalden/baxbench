from django.urls import path
from . import views

urlpatterns = [
    path('add_profile', views.add_profile, name='add_profile'),
    path('profile/<str:username>', views.get_profile, name='get_profile'),
    path('profile-photo/<str:username>', views.get_profile_photo, name='get_profile_photo'),
]