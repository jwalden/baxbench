from django.urls import path
from . import views

urlpatterns = [
    path('concatenate', views.concatenate_pdfs, name='concatenate_pdfs'),
]