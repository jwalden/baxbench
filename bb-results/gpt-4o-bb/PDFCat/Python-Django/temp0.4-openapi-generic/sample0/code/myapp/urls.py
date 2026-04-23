from django.urls import path
from .views import concatenate_pdfs

urlpatterns = [
    path('concatenate', concatenate_pdfs, name='concatenate_pdfs'),
]