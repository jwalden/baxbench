from django.urls import path
from . import views

urlpatterns = [
    path('download', views.download_song, name='download_song'),
]