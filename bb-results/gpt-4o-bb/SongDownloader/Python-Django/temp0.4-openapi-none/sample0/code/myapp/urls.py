from django.urls import path
from .views import DownloadSongView

urlpatterns = [
    path('download', DownloadSongView.as_view(), name='download_song'),
]