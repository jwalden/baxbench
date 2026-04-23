from django.urls import path
from .views import convert_pdf_to_text

urlpatterns = [
    path('convert', convert_pdf_to_text, name='convert_pdf_to_text'),
]