from django.urls import path
from .views import search_files

urlpatterns = [
    path('search', search_files, name='search_files'),
]