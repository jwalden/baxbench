from django.urls import path
from .views import FileSearchView

urlpatterns = [
    path('search', FileSearchView.as_view(), name='file_search'),
]