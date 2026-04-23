from django.urls import path
from . import views

urlpatterns = [
    path('search', views.search_files, name='search_files'),
]