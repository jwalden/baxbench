from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload_image, name='upload_image'),
    path('images/<int:imageId>', views.view_image, name='view_image'),
]