from django.urls import path
from . import views

urlpatterns = [
    path('convert', views.convert_pdf_to_text, name='convert_pdf_to_text'),
]