from django.urls import path
from .views import convert_zip_to_txt

urlpatterns = [
    path('convert', convert_zip_to_txt),
]