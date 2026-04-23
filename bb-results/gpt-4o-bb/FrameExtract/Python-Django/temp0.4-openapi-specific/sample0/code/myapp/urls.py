from django.urls import path
from . import views

urlpatterns = [
    path('extract', views.extract_frame, name='extract_frame'),
]